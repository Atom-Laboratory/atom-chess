#include "board/move_applier.hpp"

#include <cstdlib>

namespace ac::chess {
namespace {

/**
 * @brief Revokes a rook-specific castling right after a rook moves from,
 *        or is captured on, its original home square.
 * @param rights Mutable castling-right snapshot.
 * @param color Color of the rook whose right may be revoked.
 * @param square Rook source or capture square.
 */
void revokeRookRight(CastlingRights& rights, PieceColor color, Square square)
{
    if (color == PieceColor::White && square.row == 7) {
        if (square.col == 0) rights.whiteQueenSide = false;
        if (square.col == 7) rights.whiteKingSide = false;
    } else if (color == PieceColor::Black && square.row == 0) {
        if (square.col == 0) rights.blackQueenSide = false;
        if (square.col == 7) rights.blackKingSide = false;
    }
}

/**
 * @brief Revokes both castling rights after a king moves.
 * @param rights Mutable castling-right snapshot.
 * @param color Color of the moving king.
 */
void revokeKingRights(CastlingRights& rights, PieceColor color)
{
    if (color == PieceColor::White) {
        rights.whiteKingSide = false;
        rights.whiteQueenSide = false;
    } else if (color == PieceColor::Black) {
        rights.blackKingSide = false;
        rights.blackQueenSide = false;
    }
}

} // namespace

void MoveApplier::moveCastlingRook(Board& board, const Move& move)
{
    const bool kingSide = move.to.col > move.from.col;
    const int rookSourceColumn = kingSide ? 7 : 0;
    const int rookTargetColumn = kingSide ? 5 : 3;

    const Square rookSource{move.from.row, rookSourceColumn};
    const Square rookTarget{move.from.row, rookTargetColumn};
    const Piece rook = board.pieceAt(rookSource);

    board.setPiece(rookSource, Piece{});
    board.setPiece(rookTarget, rook);
}

void MoveApplier::removeEnPassantPawn(Board& board, const Move& move)
{
    const Square capturedPawnSquare{move.from.row, move.to.col};
    board.setPiece(capturedPawnSquare, Piece{});
}

void MoveApplier::apply(Board& board, const Move& move)
{
    Piece movingPiece = board.pieceAt(move.from);
    const bool wasPawn = movingPiece.type == PieceType::Pawn;
    const Piece targetPiece = board.pieceAt(move.to);
    const bool isCapture = move.capture
        || move.enPassant
        || targetPiece.type != PieceType::None;

    CastlingRights rights = board.castlingRights();

    if (movingPiece.type == PieceType::King) {
        revokeKingRights(rights, movingPiece.color);
    } else if (movingPiece.type == PieceType::Rook) {
        revokeRookRight(rights, movingPiece.color, move.from);
    }

    if (targetPiece.type == PieceType::Rook) {
        revokeRookRight(rights, targetPiece.color, move.to);
    }

    board.setPiece(move.from, Piece{});

    if (move.enPassant) {
        removeEnPassantPawn(board, move);
    }

    if (move.promotion != PieceType::None) {
        movingPiece.type = move.promotion;
    }

    board.setPiece(move.to, movingPiece);

    if (move.castle) {
        moveCastlingRook(board, move);
    }

    board.setCastlingRights(rights);

    if (wasPawn && std::abs(move.to.row - move.from.row) == 2) {
        board.setEnPassantTarget(Square{
            (move.to.row + move.from.row) / 2,
            move.from.col
        });
    } else {
        board.setEnPassantTarget(std::nullopt);
    }

    if (wasPawn || isCapture) {
        board.setHalfmoveClock(0);
    } else {
        board.setHalfmoveClock(board.halfmoveClock() + 1);
    }

    if (movingPiece.color == PieceColor::Black) {
        board.setFullmoveNumber(board.fullmoveNumber() + 1);
    }

    board.setSideToMove(
        movingPiece.color == PieceColor::White
            ? PieceColor::Black
            : PieceColor::White
    );
}

} // namespace ac::chess
