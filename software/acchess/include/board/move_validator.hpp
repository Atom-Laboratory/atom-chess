#pragma once

#include <optional>
#include <vector>

#include "board/board.hpp"
#include "board/move.hpp"
#include "board/square_change.hpp"

namespace ac::chess {

/**
 * @class MoveValidator
 * @brief Interprets an observed board transition as one legal chess move.
 *
 * MoveValidator belongs to Chess Core and never mutates the authoritative
 * Board. It compares a previously accepted Board state with either a newly
 * observed Board or an explicit list of SquareChange values.
 *
 * Validation covers piece geometry, path obstruction, captures, promotions,
 * king safety, castling and en passant. History-dependent rules are resolved
 * from authoritative Board metadata, never from Vision geometry alone.
 *
 * @note This class validates chess-domain legality only. It does not execute
 *       robot motion or communicate with the ESP32-S3.
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
