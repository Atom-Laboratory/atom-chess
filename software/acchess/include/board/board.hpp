#pragma once

#include "board/piece.hpp"
#include "board/move.hpp"
#include "board/square.hpp"
#include <array>
#include <optional>

/**
 * @struct CastlingRights
 * @brief Tracks which castling moves are still legally available for each side.
 */
struct CastlingRights {
    bool whiteKingSide  = true;
    bool whiteQueenSide = true;
    bool blackKingSide  = true;
    bool blackQueenSide = true;

    bool operator==(const CastlingRights&) const = default;
};

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

        // ==========================================
        // Board State metadata
        // ==========================================
        // Exposed so that modules such as FenGenerator can serialize the
        // full game state without depending on Computer Vision or Motion
        // Planning.

        /// @brief Color of the side to move next.
        PieceColor sideToMove() const;
        void setSideToMove(PieceColor color);

        /// @brief Castling availability for both sides.
        const CastlingRights& castlingRights() const;
        void setCastlingRights(const CastlingRights& rights);

        /// @brief Target square for an en passant capture, if any.
        std::optional<Square> enPassantTarget() const;
        void setEnPassantTarget(std::optional<Square> target);

        /// @brief Number of halfmoves since the last capture or pawn advance.
        int halfmoveClock() const;
        void setHalfmoveClock(int halfmoveClock);

        /// @brief Number of the current full move, starting at 1.
        int fullmoveNumber() const;
        void setFullmoveNumber(int fullmoveNumber);

    private:

        std::array<std::array<Piece,8>,8> board_;

        PieceColor sideToMove_ = PieceColor::White;
        CastlingRights castlingRights_;
        std::optional<Square> enPassantTarget_;
        int halfmoveClock_ = 0;
        int fullmoveNumber_ = 1;
};