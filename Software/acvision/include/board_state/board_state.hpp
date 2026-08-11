#ifndef AC_BOARD_STATE_HPP
#define AC_BOARD_STATE_HPP

#include <array>

namespace ac
{

/**
 * @enum CellState
 * @brief Represents the visual state of a board cell.
 */
enum class CellState
{
    EMPTY,  /**< Empty square */
    WHITE,  /**< White piece */
    BLACK   /**< Black piece */
};

/**
 * @struct BoardState
 * @brief Represents the complete visual state of the chessboard.
 *
 * Each position in the 8x8 matrix represents one board cell.
 */
struct BoardState
{
    std::array<std::array<CellState, 8>, 8> cells{};
};

}

#endif