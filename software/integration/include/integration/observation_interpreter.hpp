#pragma once

#include <optional>
#include <vector>

#include "board_observation/board_observation.hpp"
#include "board/board.hpp"
#include "board/move.hpp"
#include "board/square_change.hpp"

namespace ac::integration {

/**
 * @struct ObservationValidationResult
 * @brief Outcome of interpreting vision observations into a chess move.
 */
struct ObservationValidationResult {
    enum class Status {
        ValidMove,             /**< A single legal chess move was recognized and applied. */
        NoChange,              /**< Previous and current observations are identical. */
        AmbiguousObservation, /**< Changes do not map to a coherent piece transition. */
        IllegalMove            /**< Changes represent a move, but it violates chess rules. */
    };

    Status status;
    std::optional<chess::Move> move;
};

/**
 * @brief Pure helper that computes SquareChanges from visual diffs against the authoritative board.
 *
 * @param officialBoard Authoritative game state before the move.
 * @param previousObservation Visual state before the move.
 * @param currentObservation Visual state after the move.
 * @return List of SquareChange records matching MoveValidator expectations.
 */
[[nodiscard]] std::vector<chess::SquareChange> extractSquareChanges(
    const chess::Board& officialBoard,
    const ac::BoardObservation& previousObservation,
    const ac::BoardObservation& currentObservation
);

/**
 * @brief Interprets physical board observations and updates the authoritative Board state if valid.
 *
 * @param officialBoard Authoritative game state to be validated against and updated.
 * @param previousObservation Visual state of the board before the human move.
 * @param currentObservation Visual state of the board after the human move.
 * @return ObservationValidationResult containing the outcome and the validated move (if any).
 */
ObservationValidationResult interpretObservation(
    chess::Board& officialBoard,
    const ac::BoardObservation& previousObservation,
    const ac::BoardObservation& currentObservation
);

} // namespace ac::integration