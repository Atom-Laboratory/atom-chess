#pragma once

#include <optional>
#include <vector>

#include "board/board.hpp"
#include "board/move.hpp"
#include "board/square_change.hpp"

namespace ac::chess {

/**
 * @brief Interprets observed board changes as one legal move.
 *
 * History-dependent legality is evaluated from the authoritative Board
 * metadata (castling rights and en-passant target).
 */
class MoveValidator {
public:
    [[nodiscard]] static std::optional<Move> validate(
        const Board& previous,
        const Board& observed,
        PieceColor sideToMove
    );

    [[nodiscard]] static std::optional<Move> validate(
        const Board& previous,
        const std::vector<SquareChange>& changes,
        PieceColor sideToMove
    );
};

} // namespace ac::chess
