#pragma once

#include <optional>

#include "board/board.hpp"
#include "board/move.hpp"
#include "board_observation/board_observation.hpp"

namespace ac::integration {

/**
 * @enum ObservationStatus
 * @brief Result category produced when interpreting one visual board observation.
 */
enum class ObservationStatus {
    ValidMove,            ///< Exactly one legal move was inferred.
    NoChange,             ///< Observation matches the current official position.
    PromotionRequired,    ///< A pawn reached the last rank but Vision cannot identify the promoted type.
    AmbiguousObservation, ///< Observation is structurally insufficient or admits multiple interpretations.
    IllegalMove           ///< A unique candidate was inferred but rejected by Chess Core.
};

/**
 * @struct ObservationValidationResult
 * @brief Immutable result of translating visual occupancy/color information into chess semantics.
 */
struct ObservationValidationResult {
    ObservationStatus status{ObservationStatus::AmbiguousObservation}; ///< Interpretation outcome.
    std::optional<ac::chess::Move> move{}; ///< Present only for ValidMove.
};

/**
 * @class ObservationInterpreter
 * @brief Bridges BoardObservation from Vision to MoveValidator in Chess Core.
 *
 * The interpreter runs on the Linux SBC/Brain. It never mutates the official
 * Board, never generates FEN, and never executes robot motion.
 *
 * Vision provides only EMPTY/WHITE/BLACK observations. Piece identity is
 * therefore inferred from the previous authoritative Board when possible.
 * Promotion is deliberately not guessed and is surfaced as PromotionRequired.
 */
class ObservationInterpreter {
public:
    /**
     * @brief Interprets one new visual observation against the official Board.
     * @param officialBoard Authoritative Board before the human move.
     * @param observation Latest EMPTY/WHITE/BLACK board observation from Vision.
     * @return Structured interpretation result.
     *
     * @post officialBoard is never modified.
     * @note Legal-move decisions are delegated to MoveValidator.
     */
    [[nodiscard]] static ObservationValidationResult interpret(
        const ac::chess::Board& officialBoard,
        const ac::BoardObservation& observation
    );
};

} // namespace ac::integration
