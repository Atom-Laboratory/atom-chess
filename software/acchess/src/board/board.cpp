#include "board/board.hpp"

#include "board/move_applier.hpp"

#include <cstdint>
#include <iostream>
#include <stdexcept>

namespace ac::chess {
namespace {

constexpr int boardSize = 8;

void validateSquare(Square square)
{
    if (square.row < 0 || square.row >= boardSize
        || square.col < 0 || square.col >= boardSize) {
        throw std::out_of_range("Square is outside the board");
    }
}

} // namespace

Board::Board()
{
    reset();
}

Piece Board::pieceAt(Square square) const
{
    validateSquare(square);
    return board_[square.row][square.col];
}

void Board::setPiece(Square square, Piece piece)
{
    validateSquare(square);
    board_[square.row][square.col] = piece;
}

void Board::reset()
{
    clear();

    board_[0][0] = {PieceType::Rook, PieceColor::Black};
    board_[0][1] = {PieceType::Knight, PieceColor::Black};
    board_[0][2] = {PieceType::Bishop, PieceColor::Black};
    board_[0][3] = {PieceType::Queen, PieceColor::Black};
    board_[0][4] = {PieceType::King, PieceColor::Black};
    board_[0][5] = {PieceType::Bishop, PieceColor::Black};
    board_[0][6] = {PieceType::Knight, PieceColor::Black};
    board_[0][7] = {PieceType::Rook, PieceColor::Black};

    for (std::uint8_t column = 0; column < boardSize; ++column) {
        board_[1][column] = {PieceType::Pawn, PieceColor::Black};
        board_[6][column] = {PieceType::Pawn, PieceColor::White};
    }

    board_[7][0] = {PieceType::Rook, PieceColor::White};
    board_[7][1] = {PieceType::Knight, PieceColor::White};
    board_[7][2] = {PieceType::Bishop, PieceColor::White};
    board_[7][3] = {PieceType::Queen, PieceColor::White};
    board_[7][4] = {PieceType::King, PieceColor::White};
    board_[7][5] = {PieceType::Bishop, PieceColor::White};
    board_[7][6] = {PieceType::Knight, PieceColor::White};
    board_[7][7] = {PieceType::Rook, PieceColor::White};
}

void Board::printBoard()
{
    for (std::uint8_t row = 0; row < boardSize; ++row) {
        for (std::uint8_t column = 0; column < boardSize; ++column) {
            const Piece piece = pieceAt({row, column});
            std::cout << "(" << static_cast<int>(piece.type)
                      << "," << static_cast<int>(piece.color) << ") ";
        }
        std::cout << '\n';
    }
}

bool Board::isSqrEmpty(Square square) const
{
    return pieceAt(square) == Piece{};
}

void Board::clear()
{
    for (auto& row : board_) {
        for (auto& piece : row) {
            piece = Piece{};
        }
    }
}

bool Board::operator==(const Board& other) const
{
    return board_ == other.board_;
}

bool Board::operator!=(const Board& other) const
{
    return !(*this == other);
}

void Board::makeMove(const Move& move)
{
    MoveApplier::apply(*this, move);
}

} // namespace ac::chess
