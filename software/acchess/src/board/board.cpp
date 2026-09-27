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
    if (!isValid(piece)) {
        throw std::invalid_argument("Invalid piece encoding");
    }
    board_[square.row][square.col] = piece;
}

void Board::reset()
{
    clear();

    sideToMove_ = PieceColor::White;
    castlingRights_ = CastlingRights{};
    enPassantTarget_.reset();
    halfmoveClock_ = 0;
    fullmoveNumber_ = 1;

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
    return board_ == other.board_
        && sideToMove_ == other.sideToMove_
        && castlingRights_ == other.castlingRights_
        && enPassantTarget_ == other.enPassantTarget_
        && halfmoveClock_ == other.halfmoveClock_
        && fullmoveNumber_ == other.fullmoveNumber_;
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


PieceColor Board::sideToMove() const noexcept
{
    return sideToMove_;
}

void Board::setSideToMove(PieceColor color)
{
    if (color == PieceColor::None) {
        throw std::invalid_argument("Side to move cannot be None");
    }
    sideToMove_ = color;
}

const CastlingRights& Board::castlingRights() const noexcept
{
    return castlingRights_;
}

void Board::setCastlingRights(const CastlingRights& rights) noexcept
{
    castlingRights_ = rights;
}

std::optional<Square> Board::enPassantTarget() const noexcept
{
    return enPassantTarget_;
}

void Board::setEnPassantTarget(std::optional<Square> target)
{
    if (target.has_value()) {
        validateSquare(*target);
    }
    enPassantTarget_ = target;
}

int Board::halfmoveClock() const noexcept
{
    return halfmoveClock_;
}

void Board::setHalfmoveClock(int value)
{
    if (value < 0) {
        throw std::invalid_argument("Halfmove clock cannot be negative");
    }
    halfmoveClock_ = value;
}

int Board::fullmoveNumber() const noexcept
{
    return fullmoveNumber_;
}

void Board::setFullmoveNumber(int value)
{
    if (value < 1) {
        throw std::invalid_argument("Fullmove number must be at least 1");
    }
    fullmoveNumber_ = value;
}

} // namespace ac::chess
