#include "board/move_applier.hpp"

#include <cstdlib>

namespace ac::chess {
namespace {

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
}

} // namespace ac::chess
