#include "engine/stockfish_uci.hpp"
#include <algorithm>
#include <cerrno>
#include <limits>
#include <sstream>
#include <stdexcept>

#if defined(__linux__)
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/wait.h>
#endif

namespace ac::chess::engine {
namespace {
#if defined(__linux__)
using Clock = std::chrono::steady_clock;
constexpr std::size_t maxLine = 4096;
constexpr std::size_t maxResponse = 1024 * 1024;

/** @brief Recompute remaining time after EINTR; never restart the deadline. */
UciStatus waitFor(int fd, short events, Clock::time_point deadline, UciStatus error) {
    while (Clock::now() < deadline) {
        const auto remaining = std::chrono::duration_cast<std::chrono::milliseconds>(deadline - Clock::now());
        const int ms = static_cast<int>(std::min<long long>(
            std::max<long long>(1, remaining.count()), std::numeric_limits<int>::max()));
        pollfd descriptor{fd, events, 0};
        const int result = poll(&descriptor, 1, ms);
        if (result > 0) { return descriptor.revents & POLLNVAL ? error : UciStatus::Success; }
        if (result < 0 && errno != EINTR) { return error; }
    }
    return UciStatus::Timeout;
}

/** @brief Coordinate syntax only; legality belongs to Chess Core. */
bool validMove(std::string_view move) {
    return (move.size() == 4 || move.size() == 5)
        && move[0] >= 'a' && move[0] <= 'h' && move[1] >= '1' && move[1] <= '8'
        && move[2] >= 'a' && move[2] <= 'h' && move[3] >= '1' && move[3] <= '8'
        && (move.size() == 4 || std::string_view{"qrbn"}.find(move[4]) != std::string_view::npos);
}

/** @brief Parse exactly bestmove <move> [ponder <move>], including null moves. */
UciResult parseBestMove(std::istringstream& input) {
    std::string move, token, ponder;
    if (!(input >> move)) { return {UciStatus::MalformedResponse, {}}; }
    const bool noMove = move == "(none)" || move == "0000";
    if (!noMove && !validMove(move)) { return {UciStatus::MalformedResponse, {}}; }
    if (input >> token) {
        if (noMove || token != "ponder" || !(input >> ponder) || !validMove(ponder) || (input >> token)) {
            return {UciStatus::MalformedResponse, {}};
        }
    }
    return noMove ? UciResult{UciStatus::NoMove, {}} : UciResult{UciStatus::Success, move};
}
#endif
} // namespace

StockfishUCI::StockfishUCI(const std::string& path)
    : StockfishUCI(path, std::chrono::milliseconds{5000}) {}
StockfishUCI::StockfishUCI(const std::string& path, std::chrono::milliseconds timeout)
    : m_engine_path(path), m_timeout(timeout) {
    if (timeout.count() <= 0 || timeout > std::chrono::hours{24}) {
        throw std::invalid_argument("UCI timeout must be positive and at most 24 hours");
    }
}
StockfishUCI::~StockfishUCI() { shutdown(); }

void StockfishUCI::shutdown() noexcept {
    m_ready = false;
    m_output_buffer.clear();
#if defined(__linux__)
    if (m_pipe_in[1] != -1 && m_process_id > 0) {
        (void)send_command("quit\n", Clock::now() + std::chrono::milliseconds{50});
    }
    for (int i = 0; i < 2; ++i) {
        if (m_pipe_in[i] != -1) { close(m_pipe_in[i]); m_pipe_in[i] = -1; }
        if (m_pipe_out[i] != -1) { close(m_pipe_out[i]); m_pipe_out[i] = -1; }
    }
    if (m_process_id > 0) {
        const auto deadline = Clock::now() + std::chrono::milliseconds{100};
        while (true) {
            const auto result = waitpid(m_process_id, nullptr, WNOHANG);
            if (result == m_process_id || (result < 0 && errno == ECHILD)) { break; }
            if (Clock::now() >= deadline || (result < 0 && errno != EINTR)) {
                (void)kill(m_process_id, SIGKILL);
                while (waitpid(m_process_id, nullptr, 0) < 0 && errno == EINTR) {}
                break;
            }
            (void)poll(nullptr, 0, 1);
        }
        m_process_id = -1;
    }
#endif
}

bool StockfishUCI::init() {
    shutdown();
#if !defined(__linux__)
    return false;
#else
    // Socket input allows per-send SIGPIPE suppression without changing process signals.
    if (socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, m_pipe_in) < 0
        || pipe2(m_pipe_out, O_CLOEXEC) < 0) {
        shutdown(); return false;
    }
    m_process_id = fork();
    if (m_process_id < 0) { shutdown(); return false; }
    if (m_process_id == 0) {
        if (dup2(m_pipe_in[0], STDIN_FILENO) < 0 || dup2(m_pipe_out[1], STDOUT_FILENO) < 0
            || fcntl(STDIN_FILENO, F_SETFD, 0) < 0 || fcntl(STDOUT_FILENO, F_SETFD, 0) < 0) {
            _exit(127);
        }
        for (const int fd : {m_pipe_in[0], m_pipe_in[1], m_pipe_out[0], m_pipe_out[1]}) {
            if (fd != STDIN_FILENO && fd != STDOUT_FILENO) { close(fd); }
        }
        execlp(m_engine_path.c_str(), m_engine_path.c_str(), static_cast<char*>(nullptr));
        _exit(127);
    }
    close(m_pipe_in[0]); m_pipe_in[0] = -1;
    close(m_pipe_out[1]); m_pipe_out[1] = -1;
    if (fcntl(m_pipe_in[1], F_SETFL, O_NONBLOCK) < 0 || fcntl(m_pipe_out[0], F_SETFL, O_NONBLOCK) < 0) {
        shutdown(); return false;
    }
    const auto deadline = Clock::now() + m_timeout;
    if (send_command("uci\n", deadline) != UciStatus::Success
        || read_output("uciok", deadline).status != UciStatus::Success
        || !m_output_buffer.empty()
        || send_command("isready\n", deadline) != UciStatus::Success
        || read_output("readyok", deadline).status != UciStatus::Success
        || Clock::now() >= deadline) {
        shutdown(); return false;
    }
    m_ready = true;
    return true;
#endif
}

UciStatus StockfishUCI::send_command(std::string_view command, Deadline deadline) {
#if !defined(__linux__)
    (void)command; (void)deadline;
    return UciStatus::Unsupported;
#else
    while (!command.empty()) {
        const auto status = waitFor(m_pipe_in[1], POLLOUT, deadline, UciStatus::WriteError);
        if (status != UciStatus::Success) { return status; }
        const auto written = send(m_pipe_in[1], command.data(), command.size(), MSG_NOSIGNAL);
        if (written > 0) { command.remove_prefix(static_cast<std::size_t>(written)); }
        else if (written == 0 || (errno != EINTR && errno != EAGAIN && errno != EWOULDBLOCK)) {
            return UciStatus::WriteError;
        }
    }
    return UciStatus::Success;
#endif
}

UciResult StockfishUCI::read_output(std::string_view expected, Deadline deadline) {
#if !defined(__linux__)
    (void)expected; (void)deadline;
    return {UciStatus::Unsupported, {}};
#else
    std::size_t received = m_output_buffer.size();
    while (Clock::now() < deadline) {
        const auto end = m_output_buffer.find('\n');
        if (end != std::string::npos) {
            if (end > maxLine) { return {UciStatus::BufferLimit, {}}; }
            std::string line = m_output_buffer.substr(0, end);
            m_output_buffer.erase(0, end + 1);
            if (!line.empty() && line.back() == '\r') { line.pop_back(); }
            if (line.find('\0') != std::string::npos) { return {UciStatus::MalformedResponse, {}}; }
            std::istringstream input(line);
            std::string token, extra;
            input >> token;
            if (token == expected) {
                if (expected == "bestmove") { return parseBestMove(input); }
                return input >> extra ? UciResult{UciStatus::MalformedResponse, {}}
                                      : UciResult{UciStatus::Success, {}};
            }
            if (token == "bestmove" || token == "uciok" || token == "readyok") {
                return {UciStatus::MalformedResponse, {}};
            }
            continue;
        }
        if (m_output_buffer.size() > maxLine) { return {UciStatus::BufferLimit, {}}; }
        const auto status = waitFor(m_pipe_out[0], POLLIN, deadline, UciStatus::ReadError);
        if (status != UciStatus::Success) { return {status, {}}; }
        char buffer[1024];
        const auto count = read(m_pipe_out[0], buffer, sizeof(buffer));
        if (count > 0) {
            received += static_cast<std::size_t>(count);
            if (received > maxResponse) { return {UciStatus::BufferLimit, {}}; }
            m_output_buffer.append(buffer, static_cast<std::size_t>(count));
        } else if (count == 0) {
            return {m_output_buffer.empty() ? UciStatus::EndOfFile : UciStatus::MalformedResponse, {}};
        } else if (errno != EINTR && errno != EAGAIN && errno != EWOULDBLOCK) {
            return {UciStatus::ReadError, {}};
        }
    }
    return {UciStatus::Timeout, {}};
#endif
}

UciResult StockfishUCI::request_best_move(const std::string& fen, int depth) {
    if (!m_ready) { return {UciStatus::NotInitialized, {}}; }
    if (depth <= 0 || fen.empty() || fen.size() > 4096
        || fen.find_first_of("\r\n") != std::string::npos || fen.find('\0') != std::string::npos) {
        return {UciStatus::InvalidRequest, {}};
    }
    if (!m_output_buffer.empty()) {
        shutdown(); return {UciStatus::MalformedResponse, {}};
    }
    const auto deadline = std::chrono::steady_clock::now() + m_timeout;
    const auto status = send_command("position fen " + fen + "\ngo depth " + std::to_string(depth) + "\n", deadline);
    auto result = status == UciStatus::Success ? read_output("bestmove", deadline) : UciResult{status, {}};
    if (std::chrono::steady_clock::now() >= deadline) { result = {UciStatus::Timeout, {}}; }
    if (result.status != UciStatus::Success && result.status != UciStatus::NoMove) { shutdown(); }
    return result;
}

std::string StockfishUCI::get_best_move(const std::string& fen, int depth) {
    const auto result = request_best_move(fen, depth);
    return result.status == UciStatus::Success ? result.move : std::string{};
}
} // namespace ac::chess::engine
