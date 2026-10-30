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
 * MoveValidator belongs to Chess Core and does not mutate the authoritative
 * Board. It consumes either a complete observed Board or a list of raw
 * SquareChange values and infers one legal move for the expected side.
 *
 * History-dependent legality is resolved from Board metadata:
 * castling rights, en-passant target and side to move.
 *
 * @note Physical robot execution is outside this class. The Linux SBC performs
 *       validation; the ESP32-S3 receives already planned motion commands.
 */
class MoveValidator {
public:
    /**
     * @brief Validates a newly observed Board against the previous state.
     * @param previous Authoritative Board before the observed move.
     * @param observed Newly observed Board to interpret.
     * @param sideToMove Expected player color.
     * @return Inferred legal Move, or std::nullopt when the transition is
     *         illegal, inconsistent or ambiguous.
     * @pre sideToMove is White or Black.
     * @note sideToMove must agree with previous.sideToMove().
     */
    [[nodiscard]] static std::optional<Move> validate(
        const Board& previous,
        const Board& observed,
        PieceColor sideToMove
    );

    /**
     * @brief Validates raw square changes against the previous Board.
     * @param previous Authoritative Board before the observed move.
     * @param changes Raw square differences produced by BoardComparator.
     * @param sideToMove Expected player color.
     * @return Inferred legal Move, or std::nullopt when changes do not encode
     *         exactly one legal move.
     * @pre Every SquareChange.before matches previous at the same square.
     * @note Castling and en-passant authorization come from previous metadata.
     */
    [[nodiscard]] static std::optional<Move> validate(
        const Board& previous,
        const std::vector<SquareChange>& changes,
        PieceColor sideToMove
    );
};

} // namespace ac::chess
