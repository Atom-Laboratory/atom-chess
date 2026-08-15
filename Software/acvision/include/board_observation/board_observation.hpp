#ifndef AC_BOARD_OBSERVATION_HPP
#define AC_BOARD_OBSERVATION_HPP

#include <array>

namespace ac
{

/**
 * @enum CellObservationState
 * @brief Represents the visual state of a board cell observed by the vision module.
 */
enum class CellObservationState
{
    EMPTY, /**< Empty square */
    WHITE, /**< White piece */
    BLACK  /**< Black piece */
};

/**
 * @struct BoardObservation
 * @brief Represents the complete visual observation of the chessboard.
 *
 * Each position in the 8x8 matrix represents the observed state of one board cell.
 * This is an observation and not the official game state.
 */
struct BoardObservation
{
    std::array<std::array<CellObservationState, 8>, 8> cells{};
};

}

#endif