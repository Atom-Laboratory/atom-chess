#pragma once

#include "board/piece.hpp"
#include "board/move.hpp"
#include "board/square.hpp"
class Board{
    public:
        Board();
        
        void reset();
        
        Piece pieceAt(Square sq) const;
        
        void setPiece(Square sq, Piece piece);

        void makeMove(const Move& move);

        void printBoard();
    private:

        Piece board_[8][8];
};