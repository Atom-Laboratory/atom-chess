#pragma once

#include <optional>
#include "board/board.hpp"
#include "board/move.hpp"
#include "engine/stockfish_uci.hpp"

namespace ac::integration {

/** @brief Engine protocol success is distinct from a legal chess move. */
enum class EngineMoveStatus { ValidMove, NoMove, CommunicationError, InvalidToken, IllegalMove };

/** @brief Only ValidMove carries a move; the original UCI status is always preserved. */
struct EngineMoveResult {
    EngineMoveStatus status;
    std::optional<chess::Move> move;
    chess::engine::UciStatus uciStatus;
};

/**
 * @brief Decodes a UCI result and validates its move against the official Board.
 * @param officialBoard Current authoritative position, never modified.
 * @param response Result of a serialized engine request for this same position.
 * @return Canonical legal move, explicit NoMove, communication error, invalid
 *         token or illegal move. No failure carries a planner-usable Move.
 * @note Coordinates use row 0 = rank 8 and column 0 = file a. NoMove does not
 *       classify checkmate/stalemate. Promotion requires an explicit q/r/b/n suffix.
 *       The caller must correlate the response with the Board used for its FEN;
 *       legality alone cannot detect a stale result that is also legal now.
 */
[[nodiscard]] EngineMoveResult validateEngineMove(
    const chess::Board& officialBoard, const chess::engine::UciResult& response);

} // namespace ac::integration
