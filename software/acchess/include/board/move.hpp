#pragma once

#include "board/square.hpp"
#include "board/piece.hpp"

namespace ac::chess {

struct Move {
    Square from;
    Square to;

    PieceType promotion = PieceType::None;

    bool capture = false;
    bool castle = false;
    bool enPassant = false;

    bool operator==(const Move& other) const;
};
}
