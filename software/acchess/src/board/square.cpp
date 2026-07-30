#include "board/square.hpp"

namespace ac::chess {

bool Square::operator==(const Square& other) const {
    return row == other.row && col == other.col;
}

}
