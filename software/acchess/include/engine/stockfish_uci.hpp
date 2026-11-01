#pragma once
#include <chrono>
#include <string>
#include <string_view>

#if defined(_WIN32) || defined(_MSC_VER)
using pid_t = int;
#else
#include <unistd.h>
#endif

namespace ac::chess::engine {

/** @brief Success means valid UCI syntax, not chess legality; only it carries a move. */
enum class UciStatus {
    Success, NoMove, Timeout, EndOfFile, ReadError, WriteError,
    MalformedResponse, BufferLimit, NotInitialized, InvalidRequest, Unsupported
};
/** @brief NoMove and all errors carry an empty move string. */
struct UciResult { UciStatus status; std::string move; };

/**
 * @brief Serialized Linux UCI session with bounded I/O and exclusive child ownership.
 * @note Not thread-safe. A failed exchange closes the session; call init() before
 *       reuse. Late results from a timed-out search cannot enter another session.
 *       No global signal disposition is changed.
 */
class StockfishUCI {
public:
    /** @brief Creates a session with a five-second total exchange budget. */
    StockfishUCI(const std::string& engine_path);
    /**
     * @brief Creates a session with a total I/O budget per handshake/search, up to 24 hours.
     * @throws std::invalid_argument for non-positive or excessive timeout.
     * @note Cleanup may use 150 ms of graceful waiting before SIGKILL/reaping.
     */
    StockfishUCI(const std::string& engine_path, std::chrono::milliseconds timeout);
    ~StockfishUCI();
    StockfishUCI(const StockfishUCI&) = delete;
    StockfishUCI& operator=(const StockfishUCI&) = delete;
    /** @brief Idempotent cleanup; escalates if the child ignores quit. */
    void shutdown() noexcept;
    /** @brief Starts/restarts the child, requiring complete uciok then readyok lines. */
    bool init();
    /**
     * @brief Returns a move token, explicit NoMove, or a typed failure.
     * @param fen_state Single-line FEN, at most 4096 bytes; no chess semantics checked here.
     * @param depth Positive search depth.
     * @note One steady-clock deadline covers writes and all fragments/info.
     *       Limits: 4096 bytes per line, 1 MiB per response.
     */
    [[nodiscard]] UciResult request_best_move(const std::string& fen_state, int depth = 15);
    /** @brief Legacy API delegates to typed operation; NoMove/errors return empty. */
    std::string get_best_move(const std::string& fen_state, int depth = 15);
private:
    using Deadline = std::chrono::steady_clock::time_point;
    UciStatus send_command(std::string_view command, Deadline deadline);
    UciResult read_output(std::string_view expected, Deadline deadline);
    std::string m_engine_path;
    std::chrono::milliseconds m_timeout;
    int m_pipe_in[2]{-1, -1};
    int m_pipe_out[2]{-1, -1};
    pid_t m_process_id{-1};
    bool m_ready{false};
    std::string m_output_buffer;
};
} // namespace ac::chess::engine
