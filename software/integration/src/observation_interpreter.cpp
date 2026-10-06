#include "integration/observation_interpreter.hpp"

#include "board/move_applier.hpp"
#include "board/move_validator.hpp"

namespace ac::integration {

namespace {

chess::PieceColor toPieceColor(ac::CellObservationState state) {
    switch (state) {
        case ac::CellObservationState::WHITE:
            return chess::PieceColor::White;
        case ac::CellObservationState::BLACK:
            return chess::PieceColor::Black;
        case ac::CellObservationState::EMPTY:
        default:
            return chess::PieceColor::None;
    }
}

} // namespace

std::vector<chess::SquareChange> extractSquareChanges(
    const chess::Board& officialBoard,
    const ac::BoardObservation& previousObservation,
    const ac::BoardObservation& currentObservation
) {
    std::vector<chess::SquareChange> changes;

    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            const auto prevCell = previousObservation.cells[row][col];
            const auto currCell = currentObservation.cells[row][col];

            if (prevCell != currCell) {
                chess::Square sq{row, col};
                chess::Piece beforePiece = officialBoard.pieceAt(sq);
                chess::Piece afterPiece{};

                if (currCell == ac::CellObservationState::EMPTY) {
                    afterPiece = chess::Piece{chess::PieceType::None, chess::PieceColor::None};
                } else {
                    afterPiece = chess::Piece{beforePiece.type, toPieceColor(currCell)};
                }

                changes.push_back(chess::SquareChange{sq, beforePiece, afterPiece});
            }
        }
    }

    return changes;
}

ObservationValidationResult interpretObservation(
    chess::Board& officialBoard,
    const ac::BoardObservation& previousObservation,
    const ac::BoardObservation& currentObservation
) {
    auto changes = extractSquareChanges(officialBoard, previousObservation, currentObservation);

    if (changes.empty()) {
        return {ObservationValidationResult::Status::NoChange, std::nullopt};
    }

    auto validatedMove = chess::MoveValidator::validate(
        officialBoard,
        changes,
        officialBoard.sideToMove()
    );

    if (!validatedMove.has_value()) {
        if (changes.size() > 4) {
            return {ObservationValidationResult::Status::AmbiguousObservation, std::nullopt};
        }
        return {ObservationValidationResult::Status::IllegalMove, std::nullopt};
    }

    chess::MoveApplier::apply(officialBoard, *validatedMove);

    return {ObservationValidationResult::Status::ValidMove, validatedMove};
}

} // namespace ac::integration