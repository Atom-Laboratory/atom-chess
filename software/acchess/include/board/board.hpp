#pragma once

#include <array>
#include <optional>

#include "board/move.hpp"
#include "board/piece.hpp"
#include "board/square.hpp"

namespace ac::chess {

struct CastlingRights {
    bool whiteKingSide{true};
    bool whiteQueenSide{true};
    bool blackKingSide{true};
    bool blackQueenSide{true};

    bool operator==(const CastlingRights&) const = default;
};

class Board {
public:
    Board();

    void reset();

    Piece pieceAt(Square square) const;
    void setPiece(Square square, Piece piece);

    [[deprecated("Use MoveApplier::apply")]]
    void makeMove(const Move& move);

    bool isSqrEmpty(Square square) const;
    void clear();

    bool operator==(const Board&) const;
    bool operator!=(const Board&) const;

    void printBoard();

    PieceColor sideToMove() const noexcept;
    void setSideToMove(PieceColor color);

    const CastlingRights& castlingRights() const noexcept;
    void setCastlingRights(const CastlingRights& rights) noexcept;

    std::optional<Square> enPassantTarget() const noexcept;
    void setEnPassantTarget(std::optional<Square> target);

    int halfmoveClock() const noexcept;
    void setHalfmoveClock(int value);

    int fullmoveNumber() const noexcept;
    void setFullmoveNumber(int value);

private:
    std::array<std::array<Piece, 8>, 8> board_{};
    PieceColor sideToMove_{PieceColor::White};
    CastlingRights castlingRights_{};
    std::optional<Square> enPassantTarget_{};
    int halfmoveClock_{0};
    int fullmoveNumber_{1};
};

} // namespace ac::chess
