#include <filesystem>
#include <iostream>
#include <string>
#include <poll.h>
#include <unistd.h>

/** Controlled UCI child; mode comes from the test-owned executable symlink. */
int main(int argc, char** argv) {
    if (argc != 1) { return 2; }
    const std::string mode = std::filesystem::path(argv[0]).filename().string();
    std::string command;
    while (std::getline(std::cin, command)) {
        if (command == "uci") {
            if (mode == "handshake-eof") { std::cout << "info string uciok\n" << std::flush; return 0; }
            if (mode == "handshake-partial") { std::cout << "uciok" << std::flush; return 0; }
            if (mode == "handshake-context") { std::cout << "readyok\n" << std::flush; return 0; }
            if (mode == "premature-ready") { std::cout << "uciok\nreadyok\n" << std::flush; continue; }
            std::cout << "id name fake\nuciok\r\n" << std::flush;
        } else if (command == "isready") {
            if (mode == "ready-incomplete") { std::cout << "info string readyok\n" << std::flush; return 0; }
            if (mode == "closed-input") { close(STDIN_FILENO); }
            std::cout << "readyok\r\n" << std::flush;
            if (mode == "closed-input") { while (true) { (void)poll(nullptr, 0, 100); } }
        } else if (command.starts_with("go ")) {
            if (mode == "eof") { return 0; }
            if (mode == "truncated") { std::cout << "bestmove e2e" << std::flush; return 0; }
            if (mode == "info-word") { std::cout << "info string bestmove e2e4\n" << std::flush; return 0; }
            if (mode == "flood") {
                for (int i = 0; i < 1000; ++i) {
                    std::cout << "info depth 1\n" << std::flush;
                    (void)poll(nullptr, 0, 2);
                }
                continue;
            }
            if (mode == "drip") {
                for (const char ch : std::string{"bestmove e2e4\n"}) {
                    std::cout << ch << std::flush;
                    (void)poll(nullptr, 0, 50);
                }
                continue;
            }
            if (mode == "limit") { std::cout << std::string(6000, 'x') << '\n' << std::flush; continue; }
            if (mode == "total-limit") {
                for (int i = 0; i < 30000; ++i) { std::cout << "info string " << std::string(80, 'x') << '\n'; }
                std::cout << std::flush;
                continue;
            }
            if (mode == "fragment") {
                for (const auto* part : {"best", "move e2", "e4\r", "\n"}) {
                    std::cout << part << std::flush;
                    (void)poll(nullptr, 0, 3);
                }
            } else if (mode == "crlf") { std::cout << "bestmove e2e4\r\n" << std::flush; }
            else if (mode == "promotion") { std::cout << "bestmove a7a8n ponder h2h1q\n" << std::flush; }
            else if (mode == "none") { std::cout << "bestmove (none)\n" << std::flush; }
            else if (mode == "zero") { std::cout << "bestmove 0000\n" << std::flush; }
            else if (mode == "badcoord") { std::cout << "bestmove i2e4\n" << std::flush; }
            else if (mode == "badpromo") { std::cout << "bestmove a7a8k\n" << std::flush; }
            else if (mode == "missing") { std::cout << "bestmove\n" << std::flush; }
            else if (mode == "trailing") { std::cout << "bestmove e2e4 junk\n" << std::flush; }
            else if (mode == "badponder") { std::cout << "bestmove e2e4 ponder\n" << std::flush; }
            else if (mode == "context") { std::cout << "readyok\n" << std::flush; }
            else if (mode == "buffered") { std::cout << "bestmove e2e4\nbestmove d2d4\n" << std::flush; }
            else { std::cout << "info string bestmove d2d4 is only commentary\nbestmove e2e4 ponder e7e5\n" << std::flush; }
        } else if (command == "quit" && mode != "ignore-quit") { return 0; }
    }
    if (mode == "ignore-quit") { while (true) { (void)poll(nullptr, 0, 100); } }
}
