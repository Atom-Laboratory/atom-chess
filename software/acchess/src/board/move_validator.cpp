#include "board/move_validator.hpp"

#include "board/board_comparator.hpp"

#include <cmath>

namespace ac::chess {
namespace {

constexpr int boardSize = 8;

bool isInside(Square square)
{
    return square.row >= 0 && square.row < boardSize
        && square.col >= 0 && square.col < boardSize;
}

bool isEmpty(Piece piece)
{
    return piece == Piece{};
}

bool hasValidEncoding(Piece piece)
{
    return (piece.type == PieceType::None) == (piece.color == PieceColor::None);
}

PieceColor opposite(PieceColor color)
{
    return color == PieceColor::White ? PieceColor::Black : PieceColor::White;
}

int pawnDirection(PieceColor color)
{
    return color == PieceColor::White ? -1 : 1;
}

int pawnStartRow(PieceColor color)
{
    return color == PieceColor::White ? 6 : 1;
}

int promotionRow(PieceColor color)
{
    return color == PieceColor::White ? 0 : 7;
}

int homeRow(PieceColor color)
{
    return color == PieceColor::White ? 7 : 0;
}

int step(int value)
{
    return (value > 0) - (value < 0);
}

bool isPromotionPiece(PieceType type)
{
    return type == PieceType::Knight
        || type == PieceType::Bishop
        || type == PieceType::Rook
        || type == PieceType::Queen;
}

bool isPathClear(const Board& board, Square from, Square to)
{
    if (from == to) {
        return false;
    }

    const int rowStep = step(to.row - from.row);
    const int colStep = step(to.col - from.col);

    for (Square square{from.row + rowStep, from.col + colStep};
         square != to;
         square = {square.row + rowStep, square.col + colStep}) {
        if (!board.isSqrEmpty(square)) {
            return false;
        }
    }

    return true;
}

std::optional<Board> buildObservedBoard(
    const Board& previous,
    const std::vector<SquareChange>& changes
)
{
    if (changes.size() < 2 || changes.size() > 4) {
        return std::nullopt;
    }

    Board observed = previous;

    for (std::size_t index = 0; index < changes.size(); ++index) {
        const SquareChange& change = changes[index];

        if (!isInside(change.square)
            || !hasValidEncoding(change.before)
            || !hasValidEncoding(change.after)
            || change.before == change.after
            || previous.pieceAt(change.square) != change.before) {
            return std::nullopt;
        }

        for (std::size_t other = index + 1; other < changes.size(); ++other) {
            if (change.square == changes[other].square) {
                return std::nullopt;
            }
        }

        observed.setPiece(change.square, change.after);
    }

    return observed;
}

std::optional<Move> inferOrdinaryMove(
    const std::vector<SquareChange>& changes,
    PieceColor sideToMove
)
{
    if (changes.size() != 2) {
        return std::nullopt;
    }

    const SquareChange* source = nullptr;
    const SquareChange* destination = nullptr;

    for (const SquareChange& change : changes) {
        if (change.before.color == sideToMove && isEmpty(change.after)) {
            if (source != nullptr) {
                return std::nullopt;
            }
            source = &change;
        }

        if (change.after.color == sideToMove
            && change.before.color != sideToMove) {
            if (destination != nullptr) {
                return std::nullopt;
            }
            destination = &change;
        }
    }

    if (source == nullptr || destination == nullptr) {
        return std::nullopt;
    }

    PieceType promotion = PieceType::None;
    if (destination->after.type != source->before.type) {
        if (source->before.type != PieceType::Pawn) {
            return std::nullopt;
        }
        promotion = destination->after.type;
    }

    return Move{
        .from = source->square,
        .to = destination->square,
        .promotion = promotion,
        .capture = !isEmpty(destination->before)
    };
}

std::optional<Move> inferEnPassant(
    const std::vector<SquareChange>& changes,
    PieceColor sideToMove
)
{
    if (changes.size() != 3) {
        return std::nullopt;
    }

    const SquareChange* source = nullptr;
    const SquareChange* destination = nullptr;
    const SquareChange* captured = nullptr;

    for (const SquareChange& change : changes) {
        if (change.before == Piece{PieceType::Pawn, sideToMove}
            && isEmpty(change.after)) {
            if (source != nullptr) {
                return std::nullopt;
            }
            source = &change;
        } else if (isEmpty(change.before)
            && change.after == Piece{PieceType::Pawn, sideToMove}) {
            if (destination != nullptr) {
                return std::nullopt;
            }
            destination = &change;
        } else if (change.before == Piece{PieceType::Pawn, opposite(sideToMove)}
            && isEmpty(change.after)) {
            if (captured != nullptr) {
                return std::nullopt;
            }
            captured = &change;
        }
    }

    if (source == nullptr || destination == nullptr || captured == nullptr) {
        return std::nullopt;
    }

    if (captured->square.row != source->square.row
        || captured->square.col != destination->square.col) {
        return std::nullopt;
    }

    return Move{
        .from = source->square,
        .to = destination->square,
        .capture = true,
        .enPassant = true
    };
}

std::optional<Move> inferCastling(
    const std::vector<SquareChange>& changes,
    PieceColor sideToMove
)
{
    if (changes.size() != 4) {
        return std::nullopt;
    }

    const Piece king{PieceType::King, sideToMove};
    const Piece rook{PieceType::Rook, sideToMove};
    const SquareChange* kingSource = nullptr;
    const SquareChange* kingDestination = nullptr;
    const SquareChange* rookSource = nullptr;
    const SquareChange* rookDestination = nullptr;

    for (const SquareChange& change : changes) {
        if (change.before == king && isEmpty(change.after)) {
            kingSource = &change;
        } else if (isEmpty(change.before) && change.after == king) {
            kingDestination = &change;
        } else if (change.before == rook && isEmpty(change.after)) {
            rookSource = &change;
        } else if (isEmpty(change.before) && change.after == rook) {
            rookDestination = &change;
        }
    }

    if (kingSource == nullptr
        || kingDestination == nullptr
        || rookSource == nullptr
        || rookDestination == nullptr) {
        return std::nullopt;
    }

    const int row = homeRow(sideToMove);
    const bool kingSide = kingDestination->square.col == 6;
    const int expectedRookSource = kingSide ? 7 : 0;
    const int expectedRookDestination = kingSide ? 5 : 3;

    if (kingSource->square != Square{row, 4}
        || kingDestination->square.row != row
        || (kingDestination->square.col != 6 && kingDestination->square.col != 2)
        || rookSource->square != Square{row, expectedRookSource}
        || rookDestination->square != Square{row, expectedRookDestination}) {
        return std::nullopt;
    }

    return Move{
        .from = kingSource->square,
        .to = kingDestination->square,
        .castle = true
    };
}

std::optional<Move> inferMove(
    const std::vector<SquareChange>& changes,
    PieceColor sideToMove
)
{
    if (changes.size() == 2) {
        return inferOrdinaryMove(changes, sideToMove);
    }
    if (changes.size() == 3) {
        return inferEnPassant(changes, sideToMove);
    }
    if (changes.size() == 4) {
        return inferCastling(changes, sideToMove);
    }
    return std::nullopt;
}

bool isPawnMoveValid(const Board& board, const Move& move, PieceColor color)
{
    const int direction = pawnDirection(color);
    const int rowDelta = move.to.row - move.from.row;
    const int colDelta = move.to.col - move.from.col;
    const Piece target = board.pieceAt(move.to);

    if (move.enPassant) {
        if (!move.capture
            || !isEmpty(target)
            || rowDelta != direction
            || std::abs(colDelta) != 1) {
            return false;
        }

        const int requiredRow = color == PieceColor::White ? 3 : 4;
        return move.from.row == requiredRow
            && board.pieceAt({move.from.row, move.to.col})
                == Piece{PieceType::Pawn, opposite(color)};
    }

    const bool captures = !isEmpty(target);
    if (move.capture != captures) {
        return false;
    }

    bool validMovement = false;
    if (captures) {
        validMovement = rowDelta == direction && std::abs(colDelta) == 1;
    } else if (colDelta == 0 && rowDelta == direction) {
        validMovement = true;
    } else if (colDelta == 0
        && rowDelta == 2 * direction
        && move.from.row == pawnStartRow(color)) {
        validMovement = board.isSqrEmpty({move.from.row + direction, move.from.col});
    }

    if (!validMovement) {
        return false;
    }

    const bool reachesPromotion = move.to.row == promotionRow(color);
    return reachesPromotion
        ? isPromotionPiece(move.promotion)
        : move.promotion == PieceType::None;
}

bool isCastlingGeometryValid(
    const Board& board,
    const Move& move,
    PieceColor color
)
{
    const int row = homeRow(color);
    if (move.from != Square{row, 4}
        || move.to.row != row
        || (move.to.col != 6 && move.to.col != 2)
        || move.capture
        || move.enPassant
        || move.promotion != PieceType::None) {
        return false;
    }

    const bool kingSide = move.to.col == 6;
    const Square rookSquare{row, kingSide ? 7 : 0};
    if (board.pieceAt(rookSquare) != Piece{PieceType::Rook, color}) {
        return false;
    }

    const int firstColumn = kingSide ? 5 : 1;
    const int lastColumn = kingSide ? 6 : 3;
    for (int column = firstColumn; column <= lastColumn; ++column) {
        if (!board.isSqrEmpty({row, column})) {
            return false;
        }
    }

    return true;
}

bool isMovementValid(
    const Board& board,
    const Move& move,
    PieceColor sideToMove
)
{
    if (!isInside(move.from) || !isInside(move.to) || move.from == move.to) {
        return false;
    }

    const Piece moving = board.pieceAt(move.from);
    const Piece target = board.pieceAt(move.to);
    if (moving.color != sideToMove
        || moving.type == PieceType::None
        || target.color == sideToMove
        || target.type == PieceType::King) {
        return false;
    }

    if (moving.type == PieceType::Pawn) {
        return isPawnMoveValid(board, move, sideToMove);
    }

    if (move.promotion != PieceType::None || move.enPassant) {
        return false;
    }

    const bool captures = !isEmpty(target);
    if (move.capture != captures) {
        return false;
    }

    const int rowDelta = move.to.row - move.from.row;
    const int colDelta = move.to.col - move.from.col;
    const int absRow = std::abs(rowDelta);
    const int absCol = std::abs(colDelta);

    switch (moving.type) {
    case PieceType::Knight:
        return !move.castle
            && ((absRow == 2 && absCol == 1)
                || (absRow == 1 && absCol == 2));
    case PieceType::Bishop:
        return !move.castle
            && absRow == absCol
            && isPathClear(board, move.from, move.to);
    case PieceType::Rook:
        return !move.castle
            && (rowDelta == 0 || colDelta == 0)
            && isPathClear(board, move.from, move.to);
    case PieceType::Queen:
        return !move.castle
            && (rowDelta == 0 || colDelta == 0 || absRow == absCol)
            && isPathClear(board, move.from, move.to);
    case PieceType::King:
        return move.castle
            ? isCastlingGeometryValid(board, move, sideToMove)
            : absRow <= 1 && absCol <= 1;
    case PieceType::None:
    case PieceType::Pawn:
        return false;
    }

    return false;
}

bool pieceAttacks(const Board& board, Square from, Square target)
{
    const Piece piece = board.pieceAt(from);
    const int rowDelta = target.row - from.row;
    const int colDelta = target.col - from.col;
    const int absRow = std::abs(rowDelta);
    const int absCol = std::abs(colDelta);

    switch (piece.type) {
    case PieceType::Pawn:
        return rowDelta == pawnDirection(piece.color) && absCol == 1;
    case PieceType::Knight:
        return (absRow == 2 && absCol == 1)
            || (absRow == 1 && absCol == 2);
    case PieceType::Bishop:
        return absRow == absCol && isPathClear(board, from, target);
    case PieceType::Rook:
        return (rowDelta == 0 || colDelta == 0)
            && isPathClear(board, from, target);
    case PieceType::Queen:
        return (rowDelta == 0 || colDelta == 0 || absRow == absCol)
            && isPathClear(board, from, target);
    case PieceType::King:
        return absRow <= 1 && absCol <= 1;
    case PieceType::None:
        return false;
    }

    return false;
}

bool isSquareAttacked(const Board& board, Square square, PieceColor attacker)
{
    for (int row = 0; row < boardSize; ++row) {
        for (int col = 0; col < boardSize; ++col) {
            const Square source{row, col};
            if (board.pieceAt(source).color == attacker
                && pieceAttacks(board, source, square)) {
                return true;
            }
        }
    }

    return false;
}

std::optional<Square> findKing(const Board& board, PieceColor color)
{
    std::optional<Square> king;

    for (int row = 0; row < boardSize; ++row) {
        for (int col = 0; col < boardSize; ++col) {
            const Square square{row, col};
            if (board.pieceAt(square) == Piece{PieceType::King, color}) {
                if (king.has_value()) {
                    return std::nullopt;
                }
                king = square;
            }
        }
    }

    return king;
}

bool isKingSafe(const Board& board, PieceColor color)
{
    const std::optional<Square> king = findKing(board, color);
    return king.has_value()
        && !isSquareAttacked(board, *king, opposite(color));
}

bool isCastlingPathSafe(
    const Board& board,
    const Move& move,
    PieceColor color
)
{
    if (!move.castle || !isKingSafe(board, color)) {
        return !move.castle;
    }

    Board transit = board;
    const Square transitSquare{
        move.from.row,
        move.from.col + step(move.to.col - move.from.col)
    };
    transit.setPiece(move.from, Piece{});
    transit.setPiece(transitSquare, Piece{PieceType::King, color});

    return !isSquareAttacked(transit, transitSquare, opposite(color));
}

} // namespace

std::optional<Move> MoveValidator::validate(
    const Board& previous,
    const Board& observed,
    PieceColor sideToMove
)
{
    return validate(
        previous,
        BoardComparator::compare(previous, observed),
        sideToMove
    );
}

std::optional<Move> MoveValidator::validate(
    const Board& previous,
    const std::vector<SquareChange>& changes,
    PieceColor sideToMove
)
{
    if (sideToMove == PieceColor::None) {
        return std::nullopt;
    }

    const std::optional<Board> observed = buildObservedBoard(previous, changes);
    const std::optional<Move> move = inferMove(changes, sideToMove);
    if (!observed.has_value()
        || !move.has_value()
        || !isMovementValid(previous, *move, sideToMove)
        || !isCastlingPathSafe(previous, *move, sideToMove)) {
        return std::nullopt;
    }

    if (!isKingSafe(*observed, sideToMove)) {
        return std::nullopt;
    }

    return move;
}

} // namespace ac::chess
