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
    static void apply(Board& board, const Move& move);
};

} // namespace ac::chess
