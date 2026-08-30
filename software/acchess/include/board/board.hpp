#pragma once

#include <array>

#include "board/move.hpp"
#include "board/piece.hpp"
#include "board/square.hpp"

namespace ac::chess {

/**
 * @brief Represents the official chessboard state and its pieces.
 */
class Board {
public:
    Board();

    void reset();

    Piece pieceAt(Square square) const;
    void setPiece(Square square, Piece piece);

    /**
     * @brief Applies a move through MoveApplier.
     * @deprecated Prefer MoveApplier::apply for new code.
     */
    [[deprecated("Use MoveApplier::apply")]]
    void makeMove(const Move& move);

    bool isSqrEmpty(Square square) const;

    void clear();

    bool operator==(const Board&) const;
    bool operator!=(const Board&) const;

    void printBoard();

private:
    std::array<std::array<Piece, 8>, 8> board_;
};

} // namespace ac::chess
