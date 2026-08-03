#pragma once

#include "board/board.hpp"
#include "board/move.hpp"

namespace ac::chess {

/**
 * @brief Applies a previously validated move to a board.
 *
 * This class only updates the board state. It does not decide whether a move
 * is legal according to chess rules.
 */
class MoveApplier {
public:
 /** 
  * @brief Applies a validated move to the board.
  * @param board The board to be updated.
  * @param move The move to be applied.
  */
    static void apply(Board& board, const Move& move);

private:
    /**
     * @brief Moves the rook during castling.
     * @param board The board to be updated.
     * @param move The castling move to be applied.
     */
    static void moveCastlingRook(Board& board, const Move& move);
    /**
     * @brief Removes the captured pawn during an en passant move.
     * @param board The board to be updated.
     * @param move The en passant move to be applied.
     */
    static void removeEnPassantPawn(Board& board, const Move& move);
};

} // namespace ac::chess
