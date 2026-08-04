#include "board/board.hpp"
#include <iostream>
#include <cstdint>

Board::Board()
{
    reset();
}

Piece Board::pieceAt(Square sq) const
{
    return board_[sq.row][sq.col];
}

void Board::setPiece(Square sq, Piece piece)
{
    board_[sq.row][sq.col] = piece;
}

void Board::reset()
{
    clear();

    board_[0][0] = {PieceType::Rook,   PieceColor::Black};
    board_[0][1] = {PieceType::Knight, PieceColor::Black};
    board_[0][2] = {PieceType::Bishop, PieceColor::Black};
    board_[0][3] = {PieceType::Queen,  PieceColor::Black};
    board_[0][4] = {PieceType::King,   PieceColor::Black};
    board_[0][5] = {PieceType::Bishop, PieceColor::Black};
    board_[0][6] = {PieceType::Knight, PieceColor::Black};
    board_[0][7] = {PieceType::Rook,   PieceColor::Black};

    for(std::uint8_t i = 0; i<8; i++)
        board_[1][i] = {PieceType::Pawn, PieceColor::Black};

    board_[7][0] = {PieceType::Rook,   PieceColor::White};
    board_[7][1] = {PieceType::Knight, PieceColor::White};
    board_[7][2] = {PieceType::Bishop, PieceColor::White};
    board_[7][3] = {PieceType::Queen,  PieceColor::White};
    board_[7][4] = {PieceType::King,   PieceColor::White};
    board_[7][5] = {PieceType::Bishop, PieceColor::White};
    board_[7][6] = {PieceType::Knight, PieceColor::White};
    board_[7][7] = {PieceType::Rook,   PieceColor::White};

    for(int i=0;i<8;i++)
        board_[6][i] = {PieceType::Pawn, PieceColor::White};
}

void Board::printBoard(){
    for (std::uint8_t r = 0; r < 8; ++r)
    {
        for (int c = 0; c < 8; ++c)
            {
                Piece p = pieceAt({r, c});

                std::cout
                    << "("
                    << static_cast<int>(p.type)
                    << ","
                    << static_cast<int>(p.color)
                    << ") ";
            }

            std::cout << '\n';
    }
}

bool Board::isSqrEmpty(Square sq) const{
    return board_[sq.row][sq.col] == Piece{};
}

void Board::clear(){
    for (auto& row : board_){
        for (auto& piece : board_){
            piece = {};
        }
    }
}

bool Board::operator==(const Board& other) const{
    return this->board_ == other.board_;
}

bool Board::operator!=(const Board& other) const{
    return !(*this == other);
}