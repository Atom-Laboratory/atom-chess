#include "integration/observation_interpreter.hpp"

#include <vector>

#include "board/move_validator.hpp"
#include "board/square_change.hpp"

namespace ac::integration {
namespace {

/**
 * @brief Converts an authoritative Piece into the equivalent visual observation state.
 * @param piece Chess Core piece value.
 * @return EMPTY, WHITE or BLACK visual state.
 */
ac::CellObservationState observedState(ac::chess::Piece piece)
{
    if (piece.type == ac::chess::PieceType::None) {
        return ac::CellObservationState::EMPTY;
    }

    return piece.color == ac::chess::PieceColor::White
        ? ac::CellObservationState::WHITE
        : ac::CellObservationState::BLACK;
}

/**
 * @brief Converts a concrete chess color to its visual observation state.
 * @param color White or Black.
 * @return Matching visual state.
 */
ac::CellObservationState observedState(ac::chess::PieceColor color)
{
    return color == ac::chess::PieceColor::White
        ? ac::CellObservationState::WHITE
        : ac::CellObservationState::BLACK;
}

/**
 * @brief Returns the opposite concrete chess color.
 * @param color White or Black.
 * @return Opposing color.
 */
ac::chess::PieceColor opposite(ac::chess::PieceColor color)
{
    return color == ac::chess::PieceColor::White
        ? ac::chess::PieceColor::Black
        : ac::chess::PieceColor::White;
}

struct VisualDelta {
    ac::chess::Square square;
    ac::chess::Piece before;
    ac::CellObservationState after;
};

/**
 * @brief Collects only squares whose observed occupancy/color differs from the official Board.
 * @param board Authoritative pre-move Board.
 * @param observation Latest visual observation.
 * @return Changed squares in row-major order.
 */
std::vector<VisualDelta> collectVisualDeltas(
    const ac::chess::Board& board,
    const ac::BoardObservation& observation)
{
    std::vector<VisualDelta> deltas;

    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            const ac::chess::Square square{row, col};
            const ac::chess::Piece before = board.pieceAt(square);
            const auto after = observation.cells[row][col];

            if (observedState(before) != after) {
                deltas.push_back({square, before, after});
            }
        }
    }

    return deltas;
}

/**
 * @brief Identifies whether a pawn transition reaches the promotion rank.
 * @param piece Moving piece inferred from the official Board.
 * @param destination Candidate destination square.
 * @return true when Vision cannot determine the required promoted PieceType.
 */
bool requiresPromotion(
    ac::chess::Piece piece,
    ac::chess::Square destination)
{
    if (piece.type != ac::chess::PieceType::Pawn) {
        return false;
    }

    return (piece.color == ac::chess::PieceColor::White && destination.row == 0)
        || (piece.color == ac::chess::PieceColor::Black && destination.row == 7);
}

} // namespace

ObservationValidationResult ObservationInterpreter::interpret(
    const ac::chess::Board& officialBoard,
    const ac::BoardObservation& observation)
{
    const auto deltas = collectVisualDeltas(officialBoard, observation);
    if (deltas.empty()) {
        return {ObservationStatus::NoChange, std::nullopt};
    }

    const ac::chess::PieceColor side = officialBoard.sideToMove();
    const auto moverObserved = observedState(side);
    const auto opponentObserved = observedState(opposite(side));

    std::vector<VisualDelta> sources;
    std::vector<VisualDelta> destinations;
    std::vector<VisualDelta> removedOpponents;

    for (const auto& delta : deltas) {
        if (delta.before.color == side
            && delta.after == ac::CellObservationState::EMPTY) {
            sources.push_back(delta);
            continue;
        }

        if (delta.after == moverObserved
            && delta.before.color != side) {
            destinations.push_back(delta);
            continue;
        }

        if (delta.before.color == opposite(side)
            && delta.after == ac::CellObservationState::EMPTY) {
            removedOpponents.push_back(delta);
            continue;
        }

        // Any other changed color/occupancy pattern cannot be explained by one legal move.
        return {ObservationStatus::AmbiguousObservation, std::nullopt};
    }

    std::vector<ac::chess::SquareChange> changes;

    // Ordinary move, capture, promotion candidate, or en passant.
    if (sources.size() == 1 && destinations.size() == 1
        && removedOpponents.size() <= 1) {
        const auto source = sources.front();
        const auto destination = destinations.front();

        if (requiresPromotion(source.before, destination.square)) {
            return {ObservationStatus::PromotionRequired, std::nullopt};
        }

        changes.push_back({
            source.square,
            source.before,
            ac::chess::Piece{}
        });
        changes.push_back({
            destination.square,
            destination.before,
            source.before
        });

        if (removedOpponents.size() == 1) {
            const auto captured = removedOpponents.front();
            if (captured.before.type != ac::chess::PieceType::Pawn
                || captured.after != ac::CellObservationState::EMPTY
                || destination.before.type != ac::chess::PieceType::None) {
                return {ObservationStatus::AmbiguousObservation, std::nullopt};
            }

            changes.push_back({
                captured.square,
                captured.before,
                ac::chess::Piece{}
            });
        }
    }
    // Castling produces two mover sources and two mover destinations.
    else if (sources.size() == 2 && destinations.size() == 2
             && removedOpponents.empty()) {
        const VisualDelta* kingSource = nullptr;
        const VisualDelta* rookSource = nullptr;

        for (const auto& source : sources) {
            if (source.before.type == ac::chess::PieceType::King) {
                kingSource = &source;
            } else if (source.before.type == ac::chess::PieceType::Rook) {
                rookSource = &source;
            }
        }

        if (kingSource == nullptr || rookSource == nullptr) {
            return {ObservationStatus::AmbiguousObservation, std::nullopt};
        }

        const VisualDelta* kingDestination = nullptr;
        const VisualDelta* rookDestination = nullptr;

        for (const auto& destination : destinations) {
            if (destination.square.col == 2 || destination.square.col == 6) {
                kingDestination = &destination;
            } else if (destination.square.col == 3 || destination.square.col == 5) {
                rookDestination = &destination;
            }
        }

        if (kingDestination == nullptr || rookDestination == nullptr) {
            return {ObservationStatus::AmbiguousObservation, std::nullopt};
        }

        changes = {
            {kingSource->square, kingSource->before, ac::chess::Piece{}},
            {kingDestination->square, kingDestination->before, kingSource->before},
            {rookSource->square, rookSource->before, ac::chess::Piece{}},
            {rookDestination->square, rookDestination->before, rookSource->before}
        };
    } else {
        return {ObservationStatus::AmbiguousObservation, std::nullopt};
    }

    const auto move = ac::chess::MoveValidator::validate(
        officialBoard,
        changes,
        side
    );

    if (!move.has_value()) {
        return {ObservationStatus::IllegalMove, std::nullopt};
    }

    return {ObservationStatus::ValidMove, move};
}

} // namespace ac::integration
