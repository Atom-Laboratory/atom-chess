#pragma once

#include "board/square.hpp"
#include "board/piece.hpp"

struct Move {

    Square from;
    Square to;

    PieceType promotion = PieceType::None;

    bool capture = false;
    bool castle = false;
    bool enPassant = false;
};