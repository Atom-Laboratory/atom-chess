#pragma once

enum class PieceType
{
    None = 0,
    Pawn,
    Knight,
    Bishop,
    Rook,
    Queen,
    King
};

enum class PieceColor
{
    None = 0,
    White,
    Black
};

struct Piece {
    PieceType type = PieceType::None;
    PieceColor color = PieceColor::None;
    bool operator==(const Piece&) const = default;
};