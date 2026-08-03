#pragma once

#include "board/piece.hpp"
#include "board/square.hpp"

namespace ac::chess {

/**
 * @brief Describes how one square changed between two board states.
 */
struct SquareChange {
    Square square;
    Piece before;
    Piece after;

    bool operator==(const SquareChange&) const = default;
};

} // namespace ac::chess
