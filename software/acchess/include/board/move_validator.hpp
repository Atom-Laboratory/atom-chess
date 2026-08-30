#pragma once

#include "board/board.hpp"
#include "board/move.hpp"
#include "board/square_change.hpp"

#include <optional>
#include <vector>

namespace ac::chess {

/**
 * @brief Interprets observed board changes as one legal chess move.
 *
 * History-dependent rules are outside this API because the current model does
 * not store castling rights, prior moves, move counters, or past positions.
 */
class MoveValidator {
public:
    /**
     * @return The inferred move, or std::nullopt when the observation is invalid.
     */
    [[nodiscard]] static std::optional<Move> validate(
        const Board& previous,
        const Board& observed,
        PieceColor sideToMove
    );

    /**
     * @return The inferred move, or std::nullopt when the changes are invalid.
     */
    [[nodiscard]] static std::optional<Move> validate(
        const Board& previous,
        const std::vector<SquareChange>& changes,
        PieceColor sideToMove
    );
};

} // namespace ac::chess
