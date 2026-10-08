#include <gtest/gtest.h>

#include "board/board.hpp"
#include "board/move.hpp"
#include "board_observation/board_observation.hpp"
#include "integration/observation_interpreter.hpp"

using namespace ac;
using namespace ac::integration;

namespace {

BoardObservation observationFromBoard(const chess::Board& board) {
    BoardObservation obs{};
    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            auto piece = board.pieceAt(chess::Square{row, col});
            if (piece.color == chess::PieceColor::White) {
                obs.cells[row][col] = CellObservationState::WHITE;
            } else if (piece.color == chess::PieceColor::Black) {
                obs.cells[row][col] = CellObservationState::BLACK;
            } else {
                obs.cells[row][col] = CellObservationState::EMPTY;
            }
        }
    }
    return obs;
}

} // namespace

TEST(ObservationInterpreterTest, DetectsNoChangeWhenObservationsAreEqual) {
    chess::Board board;
    BoardObservation prev = observationFromBoard(board);
    BoardObservation curr = prev;

    auto result = interpretObservation(board, prev, curr);

    EXPECT_EQ(result.status, ObservationValidationResult::Status::NoChange);
    EXPECT_FALSE(result.move.has_value());
}

TEST(ObservationInterpreterTest, ValidatesAndAppliesQuietMove) {
    chess::Board board; // Posição inicial (Brancas jogam)
    BoardObservation prev = observationFromBoard(board);

    // Lance legal: e2 (row 6, col 4) -> e4 (row 4, col 4)
    BoardObservation curr = prev;
    curr.cells[6][4] = CellObservationState::EMPTY;
    curr.cells[4][4] = CellObservationState::WHITE;

    auto result = interpretObservation(board, prev, curr);

    EXPECT_EQ(result.status, ObservationValidationResult::Status::ValidMove);
    ASSERT_TRUE(result.move.has_value());
    EXPECT_EQ(result.move->from, (chess::Square{6, 4}));
    EXPECT_EQ(result.move->to, (chess::Square{4, 4}));

    // Verifica mutação segura no Board oficial
    EXPECT_EQ(board.pieceAt(chess::Square{6, 4}).type, chess::PieceType::None);
    EXPECT_EQ(board.pieceAt(chess::Square{4, 4}).type, chess::PieceType::Pawn);
    EXPECT_EQ(board.sideToMove(), chess::PieceColor::Black);
}

TEST(ObservationInterpreterTest, RejectsIllegalMoveWithoutMutatingBoard) {
    chess::Board board;
    const chess::Board boardCopy = board;
    BoardObservation prev = observationFromBoard(board);

    // Lance ilegal: Peão de e2 (row 6, col 4) pula 3 casas para e5 (row 3, col 4)
    BoardObservation curr = prev;
    curr.cells[6][4] = CellObservationState::EMPTY;
    curr.cells[3][4] = CellObservationState::WHITE;

    auto result = interpretObservation(board, prev, curr);

    EXPECT_EQ(result.status, ObservationValidationResult::Status::IllegalMove);
    EXPECT_FALSE(result.move.has_value());
    EXPECT_EQ(board, boardCopy); // Invariante: Board oficial permanece inalterado
}

TEST(ObservationInterpreterTest, RejectsAmbiguousObservationWithMultipleChanges) {
    chess::Board board;
    const chess::Board boardCopy = board;
    BoardObservation prev = observationFromBoard(board);

    // Observação ambígua: 5 alterações desconexas (mão cobrindo peças)
    BoardObservation curr = prev;
    curr.cells[6][0] = CellObservationState::EMPTY;
    curr.cells[6][1] = CellObservationState::EMPTY;
    curr.cells[6][2] = CellObservationState::EMPTY;
    curr.cells[5][0] = CellObservationState::WHITE;
    curr.cells[5][1] = CellObservationState::WHITE;

    auto result = interpretObservation(board, prev, curr);

    EXPECT_EQ(result.status, ObservationValidationResult::Status::AmbiguousObservation);
    EXPECT_FALSE(result.move.has_value());
    EXPECT_EQ(board, boardCopy); // Invariante: Board oficial permanece inalterado
}

TEST(ObservationInterpreterTest, ValidatesAndAppliesCaptureMove) {
    chess::Board board;
    // Configura cenário: Peão branco em d4 (4, 3), Peão preto em e5 (3, 4)
    board.setPiece(chess::Square{4, 3}, {chess::PieceType::Pawn, chess::PieceColor::White});
    board.setPiece(chess::Square{3, 4}, {chess::PieceType::Pawn, chess::PieceColor::Black});
    board.setPiece(chess::Square{6, 3}, chess::Piece{}); // Esvazia d2 original

    BoardObservation prev = observationFromBoard(board);

    // Lance: d4 toma e5 (row 4, col 3 -> row 3, col 4)
    BoardObservation curr = prev;
    curr.cells[4][3] = CellObservationState::EMPTY;
    curr.cells[3][4] = CellObservationState::WHITE; // Substitui peça preta por branca

    auto result = interpretObservation(board, prev, curr);

    EXPECT_EQ(result.status, ObservationValidationResult::Status::ValidMove);
    ASSERT_TRUE(result.move.has_value());
    EXPECT_EQ(result.move->from, (chess::Square{4, 3}));
    EXPECT_EQ(result.move->to, (chess::Square{3, 4}));

    // Verifica que o tabuleiro oficial foi atualizado com a captura
    EXPECT_EQ(board.pieceAt(chess::Square{4, 3}).type, chess::PieceType::None);
    EXPECT_EQ(board.pieceAt(chess::Square{3, 4}), (chess::Piece{chess::PieceType::Pawn, chess::PieceColor::White}));
    EXPECT_EQ(board.sideToMove(), chess::PieceColor::Black);
}

TEST(ObservationInterpreterTest, ValidatesAndAppliesKingsideCastling) {
    chess::Board board;
    // Libera caminho para o roque menor das brancas (esvazia f1 e g1)
    board.setPiece(chess::Square{7, 5}, chess::Piece{}); // f1 (row 7, col 5)
    board.setPiece(chess::Square{7, 6}, chess::Piece{}); // g1 (row 7, col 6)

    BoardObservation prev = observationFromBoard(board);

    // Roque menor: Rei de e1 (7, 4) para g1 (7, 6) e Torre de h1 (7, 7) para f1 (7, 5)
    BoardObservation curr = prev;
    curr.cells[7][4] = CellObservationState::EMPTY; // e1 vago
    curr.cells[7][7] = CellObservationState::EMPTY; // h1 vago
    curr.cells[7][6] = CellObservationState::WHITE; // Rei em g1
    curr.cells[7][5] = CellObservationState::WHITE; // Torre em f1

    auto result = interpretObservation(board, prev, curr);

    EXPECT_EQ(result.status, ObservationValidationResult::Status::ValidMove);
    ASSERT_TRUE(result.move.has_value());
    EXPECT_EQ(result.move->from, (chess::Square{7, 4}));
    EXPECT_EQ(result.move->to, (chess::Square{7, 6}));

    // Verifica que Rei e Torre estão em seus novos postos
    EXPECT_EQ(board.pieceAt(chess::Square{7, 6}), (chess::Piece{chess::PieceType::King, chess::PieceColor::White}));
    EXPECT_EQ(board.pieceAt(chess::Square{7, 5}), (chess::Piece{chess::PieceType::Rook, chess::PieceColor::White}));
    EXPECT_EQ(board.sideToMove(), chess::PieceColor::Black);
}
TEST(ObservationInterpreterTest, ValidatesAndAppliesEnPassantCapture) {
    chess::Board board;
    // Configura posição para En Passant das Brancas:
    // Peão branco em e5 (row 3, col 4)
    board.setPiece(chess::Square{3, 4}, {chess::PieceType::Pawn, chess::PieceColor::White});
    board.setPiece(chess::Square{6, 4}, chess::Piece{}); // Esvazia e2 original

    // Peão preto acabou de saltar de d7 (row 1, col 3) para d5 (row 3, col 3)
    board.setPiece(chess::Square{3, 3}, {chess::PieceType::Pawn, chess::PieceColor::Black});
    board.setPiece(chess::Square{1, 3}, chess::Piece{}); // Esvazia d7 original

    // Define o alvo de En Passant para d6 (row 2, col 3)
    board.setEnPassantTarget(chess::Square{2, 3});
    board.setSideToMove(chess::PieceColor::White);

    BoardObservation prev = observationFromBoard(board);

    // Lance: Peão branco toma en passant (e5 -> d6, e peão de d5 desaparece)
    // 3 casas modificadas:
    BoardObservation curr = prev;
    curr.cells[3][4] = CellObservationState::EMPTY; // e5 vago
    curr.cells[3][3] = CellObservationState::EMPTY; // d5 capturado e removido
    curr.cells[2][3] = CellObservationState::WHITE; // d6 ocupado pelo peão branco

    auto result = interpretObservation(board, prev, curr);

    EXPECT_EQ(result.status, ObservationValidationResult::Status::ValidMove);
    ASSERT_TRUE(result.move.has_value());
    EXPECT_EQ(result.move->from, (chess::Square{3, 4}));
    EXPECT_EQ(result.move->to, (chess::Square{2, 3}));

    // Verifica que o tabuleiro oficial refletiu a captura en passant
    EXPECT_EQ(board.pieceAt(chess::Square{3, 4}).type, chess::PieceType::None);
    EXPECT_EQ(board.pieceAt(chess::Square{3, 3}).type, chess::PieceType::None);
    EXPECT_EQ(board.pieceAt(chess::Square{2, 3}), (chess::Piece{chess::PieceType::Pawn, chess::PieceColor::White}));
    EXPECT_EQ(board.sideToMove(), chess::PieceColor::Black);
}