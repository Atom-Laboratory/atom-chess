#include "board/move_applier.hpp"

namespace ac::chess {

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
