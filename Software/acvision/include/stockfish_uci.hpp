#pragma once
#include <string>
#include <unistd.h>

namespace ac {

class StockfishUCI {
public:
    StockfishUCI(const std::string& engine_path);
    ~StockfishUCI();

    bool init();
    std::string get_best_move(const std::string& fen_state, int depth = 15);

private:
    std::string m_engine_path;
    
    
    int m_pipe_in[2];
    int m_pipe_out[2];
    pid_t m_process_id;

    void send_command(const std::string& command);
    std::string read_output(const std::string& stop_word);
};

}