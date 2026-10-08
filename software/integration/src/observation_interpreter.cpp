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
    struct Diff {
        chess::Square sq;
        chess::Piece before;
        ac::CellObservationState curr;
    };

    std::vector<Diff> diffs;
    std::vector<chess::Piece> vacatedPieces;

    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            const auto prevCell = previousObservation.cells[row][col];
            const auto currCell = currentObservation.cells[row][col];

            if (prevCell != currCell) {
                chess::Square sq{row, col};
                chess::Piece before = officialBoard.pieceAt(sq);
                diffs.push_back({sq, before, currCell});

                if (currCell == ac::CellObservationState::EMPTY && before.type != chess::PieceType::None) {
                    vacatedPieces.push_back(before);
                }
            }
        }
    }

    std::vector<chess::SquareChange> changes;
    changes.reserve(diffs.size());

    // Se duas peças da mesma cor se moveram simultaneamente (ex: roque Rei + Torre)
    bool isDoublePieceMove = (vacatedPieces.size() == 2 && vacatedPieces[0].color == vacatedPieces[1].color);

    for (const auto& d : diffs) {
        chess::Piece afterPiece{};

        if (d.curr == ac::CellObservationState::EMPTY) {
            afterPiece = chess::Piece{chess::PieceType::None, chess::PieceColor::None};
        } else {
            chess::PieceColor observedColor = toPieceColor(d.curr);
            chess::PieceType inferredType = chess::PieceType::None;

            if (vacatedPieces.size() == 1) {
                inferredType = vacatedPieces.front().type;
            } else if (isDoublePieceMove) {
                // No roque, o Rei para nas colunas 6 (g) ou 2 (c), e a Torre nas colunas 5 (f) ou 3 (d)
                if (d.sq.col == 6 || d.sq.col == 2) {
                    inferredType = chess::PieceType::King;
                } else if (d.sq.col == 5 || d.sq.col == 3) {
                    inferredType = chess::PieceType::Rook;
                }
            } else {
                for (const auto& vp : vacatedPieces) {
                    if (vp.color == observedColor) {
                        inferredType = vp.type;
                        break;
                    }
                }
            }

            afterPiece = chess::Piece{inferredType, observedColor};
        }

        changes.push_back(chess::SquareChange{d.sq, d.before, afterPiece});
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

    // Um lance válido no xadrez envolve 2 casas (normal/captura), 3 (en-passant) ou 4 (roque)
    if (changes.size() != 2 && changes.size() != 3 && changes.size() != 4) {
        return {ObservationValidationResult::Status::AmbiguousObservation, std::nullopt};
    }

    auto validatedMove = chess::MoveValidator::validate(
        officialBoard,
        changes,
        officialBoard.sideToMove()
    );

    if (!validatedMove.has_value()) {
        return {ObservationValidationResult::Status::IllegalMove, std::nullopt};
    }

    chess::MoveApplier::apply(officialBoard, *validatedMove);

    return {ObservationValidationResult::Status::ValidMove, validatedMove};
}

} // namespace ac::integration