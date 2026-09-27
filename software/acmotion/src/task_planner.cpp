#include "motion/task_planner.hpp"

#include <stdexcept>

namespace ac::motion {

TaskPlanner::TaskPlanner(
    const CoordinateMapper& mapper,
    GraveyardAllocator& graveyardAllocator)
    : mapper_(mapper),
      graveyardAllocator_(graveyardAllocator)
{
}

std::string TaskPlanner::toAlgebraic(ac::chess::Square square)
{
    if (square.row < 0 || square.row > 7
        || square.col < 0 || square.col > 7) {
        throw std::out_of_range("Board square is outside the 8x8 domain");
    }

    const char file = static_cast<char>('a' + square.col);
    const char rank = static_cast<char>('8' - square.row);
    return std::string{file, rank};
}

Point2D TaskPlanner::boardPoint(ac::chess::Square square) const
{
    return mapper_.boardSquare(toAlgebraic(square));
}

std::vector<PhysicalTask> TaskPlanner::planTasks(
    const ac::chess::Board& boardBeforeMove,
    const ac::chess::Move& move)
{
    const ac::chess::Piece movingPiece = boardBeforeMove.pieceAt(move.from);
    if (movingPiece.type == ac::chess::PieceType::None) {
        throw std::invalid_argument("TaskPlanner source square is empty");
    }

    std::vector<PhysicalTask> tasks;

    if (move.enPassant) {
        const ac::chess::Square capturedSquare{move.from.row, move.to.col};
        const ac::chess::Piece capturedPiece =
            boardBeforeMove.pieceAt(capturedSquare);

        if (capturedPiece.type != ac::chess::PieceType::Pawn
            || capturedPiece.color == movingPiece.color) {
            throw std::invalid_argument(
                "En-passant task requires an opposing pawn on the captured square"
            );
        }

        const Point2D graveyardTarget =
            graveyardAllocator_.allocateNext(capturedPiece);

        tasks.push_back({
            PhysicalTaskType::RemoveCapturedPiece,
            capturedPiece,
            capturedSquare,
            std::nullopt,
            boardPoint(capturedSquare),
            graveyardTarget
        });
    } else if (move.capture) {
        const ac::chess::Piece capturedPiece = boardBeforeMove.pieceAt(move.to);
        if (capturedPiece.type == ac::chess::PieceType::None
            || capturedPiece.color == movingPiece.color) {
            throw std::invalid_argument(
                "Capture task requires an opposing piece on the destination square"
            );
        }

        const Point2D graveyardTarget =
            graveyardAllocator_.allocateNext(capturedPiece);

        tasks.push_back({
            PhysicalTaskType::RemoveCapturedPiece,
            capturedPiece,
            move.to,
            std::nullopt,
            boardPoint(move.to),
            graveyardTarget
        });
    }

    tasks.push_back({
        PhysicalTaskType::MoveBoardPiece,
        movingPiece,
        move.from,
        move.to,
        boardPoint(move.from),
        boardPoint(move.to)
    });

    if (move.castle) {
        const bool kingSide = move.to.col > move.from.col;
        const ac::chess::Square rookSource{
            move.from.row,
            kingSide ? 7 : 0
        };
        const ac::chess::Square rookTarget{
            move.from.row,
            kingSide ? 5 : 3
        };
        const ac::chess::Piece rook = boardBeforeMove.pieceAt(rookSource);

        if (movingPiece.type != ac::chess::PieceType::King
            || rook.type != ac::chess::PieceType::Rook
            || rook.color != movingPiece.color) {
            throw std::invalid_argument(
                "Castling task requires matching king and rook pieces"
            );
        }

        tasks.push_back({
            PhysicalTaskType::MoveBoardPiece,
            rook,
            rookSource,
            rookTarget,
            boardPoint(rookSource),
            boardPoint(rookTarget)
        });
    }

    if (move.promotion != ac::chess::PieceType::None) {
        if (movingPiece.type != ac::chess::PieceType::Pawn) {
            throw std::invalid_argument(
                "Promotion task requires a moving pawn"
            );
        }

        tasks.push_back({
            PhysicalTaskType::PromotionRequired,
            {
                move.promotion,
                movingPiece.color
            },
            move.to,
            move.to,
            std::nullopt,
            boardPoint(move.to)
        });
    }

    return tasks;
}

} // namespace ac::motion
