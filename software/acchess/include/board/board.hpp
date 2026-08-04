#pragma once

#include "board/piece.hpp"
#include "board/move.hpp"
#include "board/square.hpp"
#include <array>
class Board{
    public:
        Board();
        
        void reset();
        
        Piece pieceAt(Square sq) const;
        void setPiece(Square sq, Piece piece);

        void makeMove(const Move& move);

        bool isSqrEmpty(Square sq) const;

        void clear();

        bool operator==(const Board&) const;
        bool operator!=(const Board&) const;

        void printBoard();
    private:

        std::array<std::array<Piece,8>,8> board_;
};