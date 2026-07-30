#ifndef AC_FEN_GENERATOR_HPP
#define AC_FEN_GENERATOR_HPP

#include <array>
#include <string>
#include "board/board.hpp"
namespace ac::chess {


/**
 * @class FenGenerator
 * @brief Responsible for converting board state into a FEN formatted string.
 *
 * This class provides a static method to generate the textual representation
 * of a chessboard based on an 8x8 matrix of CellState values.
 */
class FenGenerator
{
public:

    /**
     * @brief Generates a FEN string from the board state.
     *
     * @param board 8x8 matrix containing the state of each cell (EMPTY, WHITE, BLACK).
     * @return std::string FEN formatted string representing the board.
     *
     * @note Only piece occupancy and color are considered.
     * @note All detected pieces are represented as pawns (P/p).
     * @note Additional FEN fields are set to fixed values.
     */
    static std::string generate(
        static std::string generate(const Board& board);
    );
};

}

#endif