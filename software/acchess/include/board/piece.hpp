#pragma once
namespace ac::chess {
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

/**
 * @brief Checks whether a piece has a consistent type and color.
 */
constexpr bool isValid(Piece piece) noexcept
{
    return (piece.type == PieceType::None)
        == (piece.color == PieceColor::None);
}

} // namespace ac::chess
