#include "board/board_comparator.hpp"
#include <cstdint>

namespace ac::chess {

std::vector<SquareChange> BoardComparator::compare(
    const Board& previous,
    const Board& current
)
{
    std::vector<SquareChange> changes;
    changes.reserve(4); // the number 4 here is chosen because the max number of squares that can change in a single chess move is 4 (castling).

    for (uint8_t row = 0; row < 8; ++row) {
        for (uint8_t col = 0; col < 8; ++col) {
            const Square square{row, col};
            const Piece before = previous.pieceAt(square);
            const Piece after = current.pieceAt(square);

            if (!(before == after)) {
                changes.push_back({square, before, after});
            }
        }
    }

    return changes;
}

} // namespace ac::chess
