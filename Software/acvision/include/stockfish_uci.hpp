#pragma once
#include <string>
#include <unistd.h>

namespace ac {

/**
 * @brief Class responsible for communicating with the Stockfish chess engine using the UCI protocol via Linux Pipes.
 */
class StockfishUCI {
public:
    /**
     * @brief Constructs the Stockfish engine interface.
     * 
     * @param engine_path The file path to the Stockfish executable.
     */
    StockfishUCI(const std::string& engine_path);
    
    /**
     * @brief Destroys the Stockfish engine interface, ensuring the process is safely terminated.
     */
    ~StockfishUCI();

    /**
     * @brief Initializes the engine and performs the UCI handshake.
     * 
     * @return true if the engine responds with "readyok", false otherwise.
     */
    bool init();

    /**
     * @brief Calculates the best move for a given board state.
     * 
     * @param fen_state The current board configuration in FEN notation.
     * @param depth The search depth for the engine (default is 15).
     * @return std::string The best move calculated by the engine (e.g., "e2e4").
     */
    std::string get_best_move(const std::string& fen_state, int depth = 15);

private:
    std::string m_engine_path;
    int m_pipe_in[2];
    int m_pipe_out[2];
    pid_t m_process_id;

    /**
     * @brief Sends a string command to the Stockfish process.
     * 
     * @param command The UCI command to be executed.
     */
    void send_command(const std::string& command);

    /**
     * @brief Reads the standard output from the Stockfish process until a specific stop word is found.
     * 
     * @param stop_word The keyword to look for in the output stream (e.g., "bestmove").
     * @return std::string The parsed result string containing the target information.
     */
    std::string read_output(const std::string& stop_word);
};

} // namespace ac