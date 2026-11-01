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
        ValidMove,             /**< A single legal move matches the complete current observation. */
        NoChange,              /**< Both observations match the official board's occupancy and color. */
        AmbiguousObservation, /**< Inconsistent baseline, candidate mismatch or incoherent changes. */
        IllegalMove            /**< Changes represent a move, but it violates chess rules. */
    };

    Status status;
    std::optional<chess::Move> move;
};

/**
 * @brief Side-effect-free evaluation with a candidate only for ValidMove.
 * @note candidateBoard includes all FEN metadata derived by MoveApplier.
 */
struct ObservationEvaluation {
    ObservationValidationResult result; ///< Status and validated move, if any.
    std::optional<chess::Board> candidateBoard; ///< Complete checked position, never an official-board reference.
};

/**
 * @brief Pure helper that computes SquareChanges from visual diffs against the authoritative board.
 *
 * @param officialBoard Authoritative game state before the move.
 * @param previousObservation Visual state before the move.
 * @param currentObservation Visual state after the move.
 * @return List of SquareChange records matching MoveValidator expectations.
 * @pre previousObservation matches officialBoard's occupancy and color.
 * @note Piece continuity comes from officialBoard, not visual type recognition.
 */
[[nodiscard]] std::vector<chess::SquareChange> extractSquareChanges(
    const chess::Board& officialBoard,
    const ac::BoardObservation& previousObservation,
    const ac::BoardObservation& currentObservation
);

/**
 * @brief Evaluates observations without modifying the official board or either observation.
 * @param officialBoard Trusted logical position, including history-dependent metadata.
 * @param previousObservation Baseline that must match all 64 official squares.
 * @param currentObservation Proposed occupancy/color after one move.
 * @return Status, validated move and a checked candidate only on ValidMove.
 * @note NoChange requires a consistent baseline. Invalid cell states are rejected.
 * @note Vision cannot distinguish same-color piece types. Unconfirmed promotions
 *       remain IllegalMove: no promotion type is guessed or committed.
 * @note A future coordinator must ensure the official position is still current
 *       before committing a returned candidate; evaluation provides no concurrency control.
 */
[[nodiscard]] ObservationEvaluation evaluateObservation(
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
 * @post Only ValidMove replaces officialBoard, once, with the checked candidate.
 *       Every other result preserves piece placement and all FEN metadata.
 * @note Uses evaluateObservation; its perception and promotion limitations apply.
 */
ObservationValidationResult interpretObservation(
    chess::Board& officialBoard,
    const ac::BoardObservation& previousObservation,
    const ac::BoardObservation& currentObservation
);

} // namespace ac::integration
