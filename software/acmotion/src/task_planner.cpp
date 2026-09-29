#include "motion/task_planner.hpp"

#include <optional>
#include <stdexcept>

namespace ac::motion {

/**
 * @brief Binds logical task planning to calibrated board/graveyard geometry.
 */
TaskPlanner::TaskPlanner(
    const CoordinateMapper& mapper,
    GraveyardAllocator& graveyardAllocator)
    : mapper_(mapper),
      graveyardAllocator_(graveyardAllocator)
{
}

/**
 * @brief Converts internal row/column coordinates into algebraic board notation.
 */
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

/**
 * @brief Resolves one logical board square through CoordinateMapper.
 */
Point2D TaskPlanner::boardPoint(ac::chess::Square square) const
{
    return mapper_.boardSquare(toAlgebraic(square));
}

/**
 * @brief Decomposes one trusted chess Move into ordered physical operations.
 *
 * All structural preconditions are checked before GraveyardAllocator consumes
 * a slot, preserving allocation state if plan construction fails.
 */
std::vector<PhysicalTask> TaskPlanner::planTasks(
    const ac::chess::Board& boardBeforeMove,
    const ac::chess::Move& move)
{
    const ac::chess::Piece movingPiece = boardBeforeMove.pieceAt(move.from);
    if (movingPiece.type == ac::chess::PieceType::None) {
        throw std::invalid_argument("TaskPlanner source square is empty");
    }

    std::optional<ac::chess::Piece> capturedPiece;
    std::optional<ac::chess::Square> capturedSquare;

    if (move.enPassant) {
        capturedSquare = ac::chess::Square{move.from.row, move.to.col};
        capturedPiece = boardBeforeMove.pieceAt(*capturedSquare);

        if (capturedPiece->type != ac::chess::PieceType::Pawn
            || capturedPiece->color == movingPiece.color) {
            throw std::invalid_argument(
                "En-passant task requires an opposing pawn on the captured square"
            );
        }
    } else if (move.capture) {
        capturedSquare = move.to;
        capturedPiece = boardBeforeMove.pieceAt(*capturedSquare);
        if (capturedPiece->type == ac::chess::PieceType::None
            || capturedPiece->color == movingPiece.color) {
            throw std::invalid_argument(
                "Capture task requires an opposing piece on the destination square"
            );
        }
    }

    std::optional<ac::chess::Piece> castlingRook;
    std::optional<ac::chess::Square> rookSource;
    std::optional<ac::chess::Square> rookTarget;

    if (move.castle) {
        const bool kingSide = move.to.col > move.from.col;
        rookSource = ac::chess::Square{
            move.from.row,
            kingSide ? 7 : 0
        };
        rookTarget = ac::chess::Square{
            move.from.row,
            kingSide ? 5 : 3
        };
        castlingRook = boardBeforeMove.pieceAt(*rookSource);

        if (movingPiece.type != ac::chess::PieceType::King
            || castlingRook->type != ac::chess::PieceType::Rook
            || castlingRook->color != movingPiece.color) {
            throw std::invalid_argument(
                "Castling task requires matching king and rook pieces"
            );
        }
    }

    if (move.promotion != ac::chess::PieceType::None) {
        if (movingPiece.type != ac::chess::PieceType::Pawn) {
            throw std::invalid_argument(
                "Promotion task requires a moving pawn"
            );
        }
    }

    const Point2D movingSource = boardPoint(move.from);
    const Point2D movingTarget = boardPoint(move.to);
    const std::optional<Point2D> capturedSource = capturedSquare.has_value()
        ? std::optional<Point2D>{boardPoint(*capturedSquare)}
        : std::nullopt;
    const std::optional<Point2D> rookPhysicalSource = rookSource.has_value()
        ? std::optional<Point2D>{boardPoint(*rookSource)}
        : std::nullopt;
    const std::optional<Point2D> rookPhysicalTarget = rookTarget.has_value()
        ? std::optional<Point2D>{boardPoint(*rookTarget)}
        : std::nullopt;

    const std::size_t taskCount = 1U
        + static_cast<std::size_t>(capturedPiece.has_value())
        + static_cast<std::size_t>(castlingRook.has_value())
        + static_cast<std::size_t>(
            move.promotion != ac::chess::PieceType::None
        );

    std::vector<PhysicalTask> tasks;
    tasks.reserve(taskCount);

    if (capturedPiece.has_value()) {
        tasks.push_back({
            PhysicalTaskType::RemoveCapturedPiece,
            *capturedPiece,
            capturedSquare,
            std::nullopt,
            capturedSource,
            std::nullopt
        });
    }

    tasks.push_back({
        PhysicalTaskType::MoveBoardPiece,
        movingPiece,
        move.from,
        move.to,
        movingSource,
        movingTarget
    });

    if (castlingRook.has_value()) {
        tasks.push_back({
            PhysicalTaskType::MoveBoardPiece,
            *castlingRook,
            rookSource,
            rookTarget,
            rookPhysicalSource,
            rookPhysicalTarget
        });
    }

    if (move.promotion != ac::chess::PieceType::None) {
        tasks.push_back({
            PhysicalTaskType::PromotionRequired,
            {
                move.promotion,
                movingPiece.color
            },
            move.to,
            move.to,
            std::nullopt,
            movingTarget
        });
    }

    if (capturedPiece.has_value()) {
        tasks.front().physicalTarget =
            graveyardAllocator_.allocateNext(*capturedPiece);
    }

    return tasks;
}

} // namespace ac::motion
