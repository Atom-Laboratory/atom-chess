#pragma once

#include <array>
#include <optional>

#include "board/move.hpp"
#include "board/piece.hpp"
#include "board/square.hpp"

namespace ac::chess {

/**
 * @struct CastlingRights
 * @brief Stores castling availability for both players.
 *
 * Rights are independent flags because moving a king, moving a rook, or
 * capturing a rook may revoke only a subset of the four original rights.
 */
struct CastlingRights {
    bool whiteKingSide{true};  ///< White may castle king-side.
    bool whiteQueenSide{true}; ///< White may castle queen-side.
    bool blackKingSide{true};  ///< Black may castle king-side.
    bool blackQueenSide{true}; ///< Black may castle queen-side.

    /**
     * @brief Compares all four castling-right flags.
     * @param other Rights instance to compare.
     * @return true when every castling-right flag is equal.
     */
    bool operator==(const CastlingRights& other) const = default;
};

/**
 * @class Board
 * @brief Authoritative chess position and game-state metadata.
 *
 * Board is the single source of truth for the Chess Core. Computer Vision
 * produces observations, while Board stores the accepted logical state used
 * by validation, FEN generation, Stockfish integration, and motion planning.
 *
 * Besides the 8x8 piece placement, Board owns all history-dependent metadata
 * required by a complete FEN position: side to move, castling rights,
 * en-passant target, halfmove clock, and fullmove number.
 */
class Board {
public:
    /**
     * @brief Constructs the standard initial chess position.
     *
     * Equivalent to calling reset() on a newly created Board.
     */
    Board();

    /**
     * @brief Restores the standard initial position and initial FEN metadata.
     *
     * Resets side-to-move to White, restores KQkq castling rights, clears the
     * en-passant target, sets halfmove clock to 0 and fullmove number to 1.
     */
    void reset();

    /**
     * @brief Returns the piece currently stored at a square.
     * @param square Zero-based board coordinate.
     * @return Piece stored at the requested square.
     * @throws std::out_of_range when square is outside the 8x8 board.
     */
    Piece pieceAt(Square square) const;

    /**
     * @brief Replaces the piece stored at a square.
     * @param square Zero-based board coordinate.
     * @param piece Valid chess piece encoding or the empty Piece{} value.
     * @throws std::out_of_range when square is outside the 8x8 board.
     * @throws std::invalid_argument when piece type/color encoding is invalid.
     */
    void setPiece(Square square, Piece piece);

    /**
     * @brief Applies a move through MoveApplier.
     * @param move Previously validated move.
     * @deprecated Prefer MoveApplier::apply for new code.
     */
    [[deprecated("Use MoveApplier::apply")]]
    void makeMove(const Move& move);

    /**
     * @brief Checks whether a square contains no piece.
     * @param square Zero-based board coordinate.
     * @return true when the square contains Piece{}.
     * @throws std::out_of_range when square is outside the board.
     */
    bool isSqrEmpty(Square square) const;

    /**
     * @brief Removes every piece from the 8x8 board.
     *
     * This operation intentionally changes piece placement only. Game-state
     * metadata is preserved so tests and position construction can manipulate
     * placement independently. Use reset() to restore all state.
     */
    void clear();

    /**
     * @brief Compares piece placement and all game-state metadata.
     * @param other Board to compare.
     * @return true when both complete positions are equal.
     */
    bool operator==(const Board& other) const;

    /**
     * @brief Compares complete Board states for inequality.
     * @param other Board to compare.
     * @return true when any placement or metadata field differs.
     */
    bool operator!=(const Board& other) const;

    /**
     * @brief Prints the raw piece type/color matrix to stdout for diagnostics.
     */
    void printBoard();

    /**
     * @brief Returns the player expected to move next.
     * @return White or Black.
     */
    PieceColor sideToMove() const noexcept;

    /**
     * @brief Sets the player expected to move next.
     * @param color White or Black.
     * @throws std::invalid_argument when color is PieceColor::None.
     */
    void setSideToMove(PieceColor color);

    /**
     * @brief Returns current castling availability.
     * @return Const reference to the four castling-right flags.
     */
    const CastlingRights& castlingRights() const noexcept;

    /**
     * @brief Replaces current castling availability.
     * @param rights New rights snapshot.
     */
    void setCastlingRights(const CastlingRights& rights) noexcept;

    /**
     * @brief Returns the current FEN en-passant target.
     * @return Target square, or std::nullopt when no en-passant capture is available.
     */
    std::optional<Square> enPassantTarget() const noexcept;

    /**
     * @brief Sets or clears the FEN en-passant target.
     * @param target Board square skipped by the last two-square pawn advance,
     *        or std::nullopt to clear it.
     * @throws std::out_of_range when a provided target is outside the board.
     */
    void setEnPassantTarget(std::optional<Square> target);

    /**
     * @brief Returns the number of halfmoves since the last pawn move or capture.
     * @return Non-negative FEN halfmove clock.
     */
    int halfmoveClock() const noexcept;

    /**
     * @brief Sets the FEN halfmove clock.
     * @param value Non-negative halfmove count.
     * @throws std::invalid_argument when value is negative.
     */
    void setHalfmoveClock(int value);

    /**
     * @brief Returns the FEN fullmove number.
     * @return Fullmove number, starting at 1 and incremented after Black moves.
     */
    int fullmoveNumber() const noexcept;

    /**
     * @brief Sets the FEN fullmove number.
     * @param value Fullmove number greater than or equal to 1.
     * @throws std::invalid_argument when value is less than 1.
     */
    void setFullmoveNumber(int value);

private:
    std::array<std::array<Piece, 8>, 8> board_{}; ///< Authoritative piece placement.
    PieceColor sideToMove_{PieceColor::White}; ///< Player expected to move next.
    CastlingRights castlingRights_{}; ///< Current castling availability.
    std::optional<Square> enPassantTarget_{}; ///< Current FEN en-passant target.
    int halfmoveClock_{0}; ///< Halfmoves since last pawn move or capture.
    int fullmoveNumber_{1}; ///< Fullmove counter incremented after Black.
};

} // namespace ac::chess
