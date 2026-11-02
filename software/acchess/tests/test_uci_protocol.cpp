#include <gtest/gtest.h>
#include "engine/stockfish_uci.hpp"
#include <cerrno>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <signal.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>

using namespace std::chrono_literals;
using ac::chess::engine::StockfishUCI;
using ac::chess::engine::UciStatus;
namespace {

/** Per-test executable name selects behavior without environment or shell commands. */
class FakeEngine {
public:
    explicit FakeEngine(const std::string& mode) {
        char pattern[] = "/tmp/atom-uci-XXXXXX";
        const char* created = mkdtemp(pattern);
        if (!created) { throw std::runtime_error("mkdtemp failed"); }
        directory = created;
        path = directory + "/" + mode;
        std::filesystem::create_symlink(FAKE_UCI_ENGINE_PATH, path);
    }
    ~FakeEngine() { (void)unlink(path.c_str()); (void)rmdir(directory.c_str()); }
    std::string path;
private:
    std::string directory;
};

TEST(UciProtocolTest, CompleteHandshakeAndLegacyApi) {
    FakeEngine fake("good");
    StockfishUCI engine(fake.path, 1000ms);
    ASSERT_TRUE(engine.init());
    EXPECT_EQ(engine.get_best_move("startpos"), "e2e4");
    EXPECT_TRUE(engine.init());
    EXPECT_EQ(engine.request_best_move("startpos").status, UciStatus::Success);
    engine.shutdown();
    engine.shutdown();
    EXPECT_EQ(engine.request_best_move("startpos").status, UciStatus::NotInitialized);
}

TEST(UciProtocolTest, RejectsIncompleteAndOutOfContextHandshakes) {
    for (const auto* mode : {"handshake-eof", "handshake-partial", "handshake-context", "ready-incomplete", "premature-ready"}) {
        SCOPED_TRACE(mode);
        FakeEngine fake(mode);
        StockfishUCI engine(fake.path, 200ms);
        EXPECT_FALSE(engine.init());
        EXPECT_EQ(engine.get_best_move("startpos"), "");
    }
}

TEST(UciProtocolTest, FragmentedAndCrLfResponses) {
    for (const auto* mode : {"fragment", "crlf", "good"}) {
        SCOPED_TRACE(mode);
        FakeEngine fake(mode);
        StockfishUCI engine(fake.path, 1000ms);
        ASSERT_TRUE(engine.init());
        const auto result = engine.request_best_move("startpos");
        EXPECT_EQ(result.status, UciStatus::Success);
        EXPECT_EQ(result.move, "e2e4");
    }
}

TEST(UciProtocolTest, PromotionAndExplicitNoMove) {
    for (const auto* mode : {"promotion", "none", "zero"}) {
        SCOPED_TRACE(mode);
        FakeEngine fake(mode);
        StockfishUCI engine(fake.path, 1000ms);
        ASSERT_TRUE(engine.init());
        const auto result = engine.request_best_move("startpos");
        EXPECT_EQ(result.status, std::string{mode} == "promotion" ? UciStatus::Success : UciStatus::NoMove);
        EXPECT_EQ(result.move, std::string{mode} == "promotion" ? "a7a8n" : "");
    }
}

TEST(UciProtocolTest, MalformedResponsesNeverYieldMoves) {
    for (const auto* mode : {"badcoord", "badpromo", "missing", "trailing", "badponder", "context", "truncated"}) {
        SCOPED_TRACE(mode);
        FakeEngine fake(mode);
        StockfishUCI engine(fake.path, 1000ms);
        ASSERT_TRUE(engine.init());
        const auto result = engine.request_best_move("startpos");
        EXPECT_EQ(result.status, UciStatus::MalformedResponse);
        EXPECT_TRUE(result.move.empty());
        EXPECT_EQ(engine.request_best_move("startpos").status, UciStatus::NotInitialized);
        ASSERT_TRUE(engine.init());
        EXPECT_TRUE(engine.get_best_move("startpos").empty());
    }
}

TEST(UciProtocolTest, EofAndInfoWordsAreNotTerminalResponses) {
    for (const auto* mode : {"eof", "info-word"}) {
        FakeEngine fake(mode);
        StockfishUCI engine(fake.path, 1000ms);
        ASSERT_TRUE(engine.init());
        const auto result = engine.request_best_move("startpos");
        EXPECT_EQ(result.status, UciStatus::EndOfFile);
        EXPECT_TRUE(result.move.empty());
    }
}

TEST(UciProtocolTest, TotalDeadlineIncludesInfoAndPartialLines) {
    for (const auto* mode : {"flood", "drip"}) {
        SCOPED_TRACE(mode);
        FakeEngine fake(mode);
        StockfishUCI engine(fake.path, 500ms);
        ASSERT_TRUE(engine.init());
        const auto start = std::chrono::steady_clock::now();
        const auto result = engine.request_best_move("startpos");
        EXPECT_EQ(result.status, UciStatus::Timeout);
        EXPECT_TRUE(result.move.empty());
        EXPECT_LT(std::chrono::steady_clock::now() - start, 2s);
        EXPECT_EQ(engine.request_best_move("startpos").status, UciStatus::NotInitialized);
    }
}

TEST(UciProtocolTest, LimitsLineAndTotalResponseBuffers) {
    for (const auto* mode : {"limit", "total-limit"}) {
        FakeEngine fake(mode);
        StockfishUCI engine(fake.path, 2s);
        ASSERT_TRUE(engine.init());
        const auto result = engine.request_best_move("startpos");
        EXPECT_EQ(result.status, UciStatus::BufferLimit);
        EXPECT_TRUE(result.move.empty());
    }
}

TEST(UciProtocolTest, ClosedInputDoesNotDeliverSigpipeToTheHost) {
    FakeEngine fake("closed-input");
    StockfishUCI engine(fake.path, 1000ms);
    ASSERT_TRUE(engine.init());
    const auto result = engine.request_best_move("startpos");
    EXPECT_EQ(result.status, UciStatus::WriteError);
    EXPECT_TRUE(result.move.empty());
}

TEST(UciProtocolTest, ShutdownEscalatesWhenQuitIsIgnored) {
    FakeEngine fake("ignore-quit");
    StockfishUCI engine(fake.path, 1000ms);
    ASSERT_TRUE(engine.init());
    const auto start = std::chrono::steady_clock::now();
    engine.shutdown();
    EXPECT_LT(std::chrono::steady_clock::now() - start, 2s);
    EXPECT_TRUE(engine.init());
}

TEST(UciProtocolTest, InvalidRequestsAndBufferedOldResultsAreRejected) {
    FakeEngine fake("buffered");
    StockfishUCI engine(fake.path, 1000ms);
    ASSERT_TRUE(engine.init());
    EXPECT_EQ(engine.request_best_move("fen\nquit").status, UciStatus::InvalidRequest);
    EXPECT_EQ(engine.request_best_move(std::string("fen\0bad", 7)).status, UciStatus::InvalidRequest);
    EXPECT_EQ(engine.request_best_move(std::string(4097, 'x')).status, UciStatus::InvalidRequest);
    EXPECT_EQ(engine.request_best_move("fen", 0).status, UciStatus::InvalidRequest);
    EXPECT_EQ(engine.request_best_move("fen").status, UciStatus::Success);
    const auto result = engine.request_best_move("fen");
    EXPECT_EQ(result.status, UciStatus::MalformedResponse);
    EXPECT_TRUE(result.move.empty());
}

TEST(UciProtocolTest, InitFailuresDoNotLeakDescriptorsOrChildren) {
    const auto count = [] { return std::distance(std::filesystem::directory_iterator{"/proc/self/fd"},
                                               std::filesystem::directory_iterator{}); };
    const auto before = count();
    for (int i = 0; i < 4; ++i) {
        StockfishUCI engine("/nonexistent/atom-uci-engine", 100ms);
        EXPECT_FALSE(engine.init());
    }
    EXPECT_EQ(count(), before);
    int status = 0;
    errno = 0;
    EXPECT_EQ(waitpid(-1, &status, WNOHANG), -1);
    EXPECT_EQ(errno, ECHILD);
    EXPECT_THROW((StockfishUCI{"unused", 0ms}), std::invalid_argument);
    EXPECT_THROW((StockfishUCI{"unused", 25h}), std::invalid_argument);
}

void interruptHandler(int) {}

TEST(UciProtocolTest, InterruptsDoNotRestartTheDeadline) {
    FakeEngine fake("flood");
    // Signal handlers are changed only in this isolated death-test child.
    EXPECT_EXIT({
        StockfishUCI engine(fake.path, 500ms);
        if (!engine.init()) { _exit(2); }
        struct sigaction action{};
        action.sa_handler = interruptHandler;
        sigemptyset(&action.sa_mask);
        if (sigaction(SIGALRM, &action, nullptr) != 0) { _exit(3); }
        itimerval timer{};
        timer.it_value.tv_usec = 1000;
        timer.it_interval.tv_usec = 1000;
        if (setitimer(ITIMER_REAL, &timer, nullptr) != 0) { _exit(4); }
        const auto start = std::chrono::steady_clock::now();
        const auto result = engine.request_best_move("startpos");
        engine.shutdown();
        _exit(result.status == UciStatus::Timeout
            && std::chrono::steady_clock::now() - start < 2s ? 0 : 5);
    }, ::testing::ExitedWithCode(0), "");
}
} // namespace
