#include "stockfish_uci.hpp"
#include <iostream>
#include <string.h>
#include <sys/wait.h>
#include <sys/select.h>

namespace ac {

StockfishUCI::StockfishUCI(const std::string& engine_path) {
    m_engine_path = engine_path;
    m_process_id = -1;
}

StockfishUCI::~StockfishUCI() {
    if (m_process_id != -1) {
        send_command("quit");
        close(m_pipe_in[1]);
        close(m_pipe_out[0]);
        waitpid(m_process_id, nullptr, 0); 
    }
}

bool StockfishUCI::init() {
    if (pipe(m_pipe_in) == -1 || pipe(m_pipe_out) == -1) {
        std::cerr << "[UCI] Erro ao criar os pipes.\n";
        return false;
    }

    m_process_id = fork();

    if (m_process_id < 0) {
        std::cerr << "[UCI] Erro no fork.\n";
        return false;
    }

    if (m_process_id == 0) {
        dup2(m_pipe_in[0], STDIN_FILENO);
        dup2(m_pipe_out[1], STDOUT_FILENO);

        close(m_pipe_in[0]); close(m_pipe_in[1]);
        close(m_pipe_out[0]); close(m_pipe_out[1]);

        execlp(m_engine_path.c_str(), m_engine_path.c_str(), nullptr);
        
        exit(1);
    } else {
        close(m_pipe_in[0]);
        close(m_pipe_out[1]);
        
        send_command("uci");
        read_output("uciok"); 
        
        send_command("isready");
        read_output("readyok"); 
        
        return true;
    }
}

void StockfishUCI::send_command(const std::string& command) {
    std::string cmd = command + "\n"; 
    write(m_pipe_in[1], cmd.c_str(), cmd.size());
}

std::string StockfishUCI::read_output(const std::string& stop_word) {
    std::string result = "";
    char buffer[256];
    ssize_t bytes_read;

    
    fd_set read_fds;
    struct timeval tv;

    while (true) {
        FD_ZERO(&read_fds);
        FD_SET(m_pipe_out[0], &read_fds);

        
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
}

std::string StockfishUCI::get_best_move(const std::string& fen_state, int depth) {
    send_command("position fen " + fen_state);
    send_command("go depth " + std::to_string(depth));
    return read_output("bestmove"); 
}

}