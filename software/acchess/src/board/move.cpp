#include "board/move.hpp"

namespace ac::chess {

bool Move::operator==(const Move& other) const {
    return from == other.from &&
           to == other.to &&
           promotion == other.promotion &&
           capture == other.capture &&
           castle == other.castle &&
           enPassant == other.enPassant;
}

}
