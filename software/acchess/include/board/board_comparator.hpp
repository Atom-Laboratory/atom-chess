#pragma once

#include "board/board.hpp"
#include "board/square_change.hpp"

#include <vector>

namespace ac::chess {

/**
 * @brief Compares board states without interpreting chess moves.
 */
class BoardComparator {
public:
    /**
     * @return All changed squares in row-major order.
     * @note The [[nodiscard]] attribute is used to indicate that the return value of this function is the main purpose of the function, thus should not be ignored.
     */
    [[nodiscard]] static std::vector<SquareChange> compare(
        const Board& previous,
        const Board& current
    );
};

} // namespace ac::chess
