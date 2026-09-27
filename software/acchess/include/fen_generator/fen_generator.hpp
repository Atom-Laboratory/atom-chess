#ifndef AC_FEN_GENERATOR_HPP
#define AC_FEN_GENERATOR_HPP

#include <string>

#include "board/board.hpp"

namespace ac::chess {

/**
 * @class FenGenerator
 * @brief Responsible for converting board state into a FEN formatted string.
 *
 * This class provides a static method to generate the textual representation
 * of a Board.
 */
class FenGenerator
{
public:
    /**
     * @brief Generates a FEN string from the board state.
     *
     * @param board Board containing the state of every square.
     * @return std::string FEN formatted string representing the board.
     *
     */
    static std::string generate(const Board& board);

private:
    static std::string serializePiecePlacement(const Board& board);
    static std::string serializeCastlingRights(const Board& board);
    static std::string serializeEnPassant(const Board& board);
    static char pieceToChar(Piece piece);
};

}

#endif
