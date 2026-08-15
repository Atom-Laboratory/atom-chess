#pragma once
#include <string>
#include <unistd.h>

namespace ac::chess::engine {

/**
 * @brief Class responsible for communicating with the Stockfish chess engine using the UCI protocol via Linux Pipes.
 * 
 * @details Inter-Process Communication (IPC) implementation using POSIX pipes.
 * This class creates a bidirectional communication channel between the main application (parent process)
 * and the Stockfish engine (child process).
 * 
 * Mechanism:
 * 1. Two unidirectional pipes are created: `m_pipe_in` (Parent -> Child) and `m_pipe_out` (Child -> Parent).
 * 2. fork() is called to duplicate the current process.
 * 3. In the Child Process: 
 *    - STDIN is redirected to read from `m_pipe_in`.
 *    - STDOUT is redirected to write to `m_pipe_out`.
 *    - execlp() replaces the child process image with the Stockfish executable.
 * 4. In the Parent Process:
 *    - write() is used on `m_pipe_in` to send UCI commands to the engine.
 *    - read() (with a select() timeout) is used on `m_pipe_out` to asynchronously capture engine responses.
 */
class StockfishUCI {
public:
    /**
     * @brief Constructs the Stockfish engine interface.
     * @param engine_path The absolute system path to the Stockfish executable.
     */
    StockfishUCI(const std::string& engine_path);
    
    /**
     * @brief Destroys the interface, ensuring the child process is gracefully terminated to prevent zombies.
     */
    ~StockfishUCI();

    /**
     * @brief Initializes the pipes, forks the process, and performs the UCI handshake.
     * @return true if the engine is successfully loaded and responds with "readyok", false otherwise.
     */
    bool init();

    /**
     * @brief Requests the engine to calculate the best move for a given board state.
     * @param fen_state The current board configuration in standard FEN notation.
     * @param depth The search depth for the engine (default is 15 plies).
     * @return std::string The best move calculated by the engine (e.g., "e2e4").
     */
    std::string get_best_move(const std::string& fen_state, int depth = 15);

private:
    std::string m_engine_path;
    int m_pipe_in[2];
    int m_pipe_out[2];
    pid_t m_process_id;

    /**
     * @brief Sends a raw string command to the Stockfish process via the input pipe.
     * @param command The standard UCI command to be executed (newline appended automatically).
     */
    void send_command(const std::string& command);

    /**
     * @brief Reads the standard output pipe from the Stockfish process until a stop word is matched.
     * @param stop_word The keyword indicating the end of a multi-line response (e.g., "bestmove" or "readyok").
     * @return std::string The parsed string containing the desired data.
     */
    std::string read_output(const std::string& stop_word);
};

} // namespace ac::chess::engine