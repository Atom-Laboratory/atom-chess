#include "engine/stockfish_uci.hpp"
#include <iostream>
#include <string.h>
#include <cerrno>

#if !defined(_WIN32) && !defined(_MSC_VER)
#include <sys/wait.h>
#include <sys/select.h>
#include <unistd.h>
#endif

namespace ac::chess::engine {

StockfishUCI::StockfishUCI(const std::string& engine_path) {
    m_engine_path = engine_path;
    m_process_id = -1;
    m_pipe_in[0] = -1; m_pipe_in[1] = -1;
    m_pipe_out[0] = -1; m_pipe_out[1] = -1;
}

StockfishUCI::~StockfishUCI() {
    shutdown();
}

void StockfishUCI::shutdown() noexcept {
#if !defined(_WIN32) && !defined(_MSC_VER)
    // Try sending the quit command gracefully if the process still exists.
    if (m_pipe_in[1] != -1 && m_process_id > 0) {
        const char* quit_cmd = "quit\n";
        auto _ = write(m_pipe_in[1], quit_cmd, 5);
        (void)_;
    }
    
    // Close all open pipes to prevent leaks.
    for (int i = 0; i < 2; ++i) {
        if (m_pipe_in[i] != -1) { close(m_pipe_in[i]); m_pipe_in[i] = -1; }
        if (m_pipe_out[i] != -1) { close(m_pipe_out[i]); m_pipe_out[i] = -1; }
    }

    // Kills orphaned processes (zombies)
    if (m_process_id > 0) {
        waitpid(m_process_id, nullptr, 0);
        m_process_id = -1;
    }
#endif
}

bool StockfishUCI::init() {
#if defined(_WIN32) || defined(_MSC_VER)
    std::cerr << "[UCI] Stockfish via POSIX pipes nao e suportado nativamente no Windows.\n";
    return false;
#else
    if (pipe(m_pipe_in) == -1 || pipe(m_pipe_out) == -1) {
        std::cerr << "[UCI] Erro ao criar os pipes de comunicacao.\n";
        shutdown();
        return false;
    }

    m_process_id = fork();

    if (m_process_id < 0) {
        std::cerr << "[UCI] Erro no fork do sistema operacional.\n";
        shutdown();
        return false;
    }

    if (m_process_id == 0) {
        // Child Process: Redirect standard I/O to pipes
        dup2(m_pipe_in[0], STDIN_FILENO);
        dup2(m_pipe_out[1], STDOUT_FILENO);

        close(m_pipe_in[0]); close(m_pipe_in[1]);
        close(m_pipe_out[0]); close(m_pipe_out[1]);

        execlp(m_engine_path.c_str(), m_engine_path.c_str(), nullptr);
        
        exit(1);
    } else {
        // Parent Process: Close unused pipe ends
        close(m_pipe_in[0]); m_pipe_in[0] = -1;
        close(m_pipe_out[1]); m_pipe_out[1] = -1;
        
        send_command("uci");
        if (read_output("uciok").empty()) {
            std::cerr << "[UCI] Erro: Falha ao inicializar o protocolo UCI ou timeout atingido.\n";
            shutdown();
            return false;
        }
        
        send_command("isready");
        if (read_output("readyok").empty()) {
            std::cerr << "[UCI] Erro: Motor nao esta pronto ou timeout atingido.\n";
            shutdown();
            return false;
        }
        
        return true;
    }
#endif
}

void StockfishUCI::send_command(const std::string& command) {
#if !defined(_WIN32) && !defined(_MSC_VER)
    std::string cmd = command + "\n"; 
    const char* data = cmd.c_str();
    size_t left = cmd.size();
    
    // A write-safe loop that handles partial writes and operating system interrupts (EINTR).
    while (left > 0) {
        ssize_t written = write(m_pipe_in[1], data, left);
        if (written < 0) {
            if (errno == EINTR) continue; // The system interrupted; try typing the rest again.
            break; // Unrecoverable error in the pipe.
        }
        data += written;
        left -= written;
    }
#else
    (void)command;
#endif
}

std::string StockfishUCI::read_output(const std::string& stop_word) {
#if !defined(_WIN32) && !defined(_MSC_VER)
    std::string result = "";
    char buffer[256];
    ssize_t bytes_read;
    fd_set read_fds;
    struct timeval tv;

    while (true) {
        FD_ZERO(&read_fds);
        FD_SET(m_pipe_out[0], &read_fds);

        // 5 second timeout to prevent indefinite blocking
        tv.tv_sec = 5;
        tv.tv_usec = 0;

        int ret = select(m_pipe_out[0] + 1, &read_fds, NULL, NULL, &tv);

        if (ret == -1) {
            std::cerr << "[UCI] Erro de leitura no pipe.\n";
            break;
        } else if (ret == 0) {
            std::cerr << "[UCI] TIMEOUT: O Stockfish nao respondeu a tempo (esperando: " << stop_word << ").\n";
            break;
        }

        bytes_read = read(m_pipe_out[0], buffer, sizeof(buffer) - 1);
        if (bytes_read <= 0) break;

        buffer[bytes_read] = '\0';
        result += buffer;

        size_t pos = result.find(stop_word);
        if (pos != std::string::npos) {
            if (stop_word == "bestmove") {
                size_t move_start = pos + 9;
                size_t move_end = result.find_first_of(" \n", move_start);
                return result.substr(move_start, move_end - move_start); 
            }
            break;
        }
    }
    return result;
#else
    (void)stop_word;
    return "";
#endif
}

std::string StockfishUCI::get_best_move(const std::string& fen_state, int depth) {
    send_command("position fen " + fen_state);
    send_command("go depth " + std::to_string(depth));
    return read_output("bestmove"); 
}

} // namespace ac::chess::engine