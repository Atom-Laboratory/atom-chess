#include <gtest/gtest.h>

#include "board/board.hpp"
#include "board/move.hpp"
#include "fen_generator/fen_generator.hpp"
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

TEST(ObservationInterpreterTest, RejectsInconsistentNoChangeAtEverySquare) {
    chess::Board board;
    board.setCastlingRights({false, true, false, true});
    board.setEnPassantTarget(chess::Square{2, 3});
    board.setHalfmoveClock(9);
    board.setFullmoveNumber(23);
    const chess::Board original = board;
    const auto fen = chess::FenGenerator::generate(board);

    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            SCOPED_TRACE(row * 8 + col);
            auto observation = observationFromBoard(board);
            auto& cell = observation.cells[row][col];
            cell = cell == CellObservationState::EMPTY
                ? CellObservationState::WHITE : CellObservationState::EMPTY;
            const auto result = interpretObservation(board, observation, observation);
            EXPECT_EQ(result.status, ObservationValidationResult::Status::AmbiguousObservation);
            EXPECT_FALSE(result.move.has_value());
            EXPECT_EQ(board, original);
            EXPECT_EQ(chess::FenGenerator::generate(board), fen);
        }
    }
}

TEST(ObservationInterpreterTest, RejectsLegalMoveWithAnUnchangedBaselineMismatch) {
    chess::Board board;
    const chess::Board original = board;
    auto previous = observationFromBoard(board);
    previous.cells[0][0] = CellObservationState::EMPTY;
    auto current = previous;
    current.cells[6][4] = CellObservationState::EMPTY;
    current.cells[4][4] = CellObservationState::WHITE;

    const auto result = interpretObservation(board, previous, current);
    EXPECT_EQ(result.status, ObservationValidationResult::Status::AmbiguousObservation);
    EXPECT_FALSE(result.move.has_value());
    EXPECT_EQ(board, original);
}

TEST(ObservationInterpreterTest, RejectsAdditionalChangesOutsideTheMove) {
    chess::Board board;
    const chess::Board original = board;
    const auto previous = observationFromBoard(board);

    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            if ((row == 6 || row == 4) && col == 4) {
                continue;
            }
            SCOPED_TRACE(row * 8 + col);
            auto current = previous;
            current.cells[6][4] = CellObservationState::EMPTY;
            current.cells[4][4] = CellObservationState::WHITE;
            auto& extra = current.cells[row][col];
            extra = extra == CellObservationState::EMPTY
                ? CellObservationState::BLACK : CellObservationState::EMPTY;
            const auto result = interpretObservation(board, previous, current);
            EXPECT_NE(result.status, ObservationValidationResult::Status::ValidMove);
            EXPECT_FALSE(result.move.has_value());
            EXPECT_EQ(board, original);
        }
    }
}

TEST(ObservationInterpreterTest, RejectsUnknownCellStatesWithoutMutation) {
    chess::Board board;
    const chess::Board original = board;
    const auto previous = observationFromBoard(board);
    auto current = previous;
    current.cells[6][4] = CellObservationState::EMPTY;
    // NOLINTNEXTLINE(clang-analyzer-optin.core.EnumCastOutOfRange) -- Deliberately malformed sensor input.
    current.cells[4][4] = static_cast<CellObservationState>(99);
    const auto result = interpretObservation(board, previous, current);
    EXPECT_NE(result.status, ObservationValidationResult::Status::ValidMove);
    EXPECT_FALSE(result.move.has_value());
    EXPECT_EQ(board, original);
}

TEST(ObservationInterpreterTest, PreservesAllFenFieldsOnIllegalMove) {
    chess::Board board;
    board.setSideToMove(chess::PieceColor::Black);
    board.setCastlingRights({false, true, true, false});
    board.setEnPassantTarget(chess::Square{5, 4});
    board.setHalfmoveClock(8);
    board.setFullmoveNumber(23);
    const chess::Board original = board;
    const auto fen = chess::FenGenerator::generate(board);
    const auto previous = observationFromBoard(board);
    auto current = previous;
    current.cells[1][4] = CellObservationState::EMPTY;
    current.cells[4][4] = CellObservationState::BLACK;

    const auto result = interpretObservation(board, previous, current);
    EXPECT_EQ(result.status, ObservationValidationResult::Status::IllegalMove);
    EXPECT_FALSE(result.move.has_value());
    EXPECT_EQ(board, original);
    EXPECT_EQ(chess::FenGenerator::generate(board), fen);
}

TEST(ObservationInterpreterTest, CommitsBlackMoveMetadataExactlyOnce) {
    chess::Board board;
    board.setSideToMove(chess::PieceColor::Black);
    board.setHalfmoveClock(8);
    board.setFullmoveNumber(23);
    const auto previous = observationFromBoard(board);
    auto current = previous;
    current.cells[0][6] = CellObservationState::EMPTY;
    current.cells[2][5] = CellObservationState::BLACK;

    const auto result = interpretObservation(board, previous, current);
    ASSERT_EQ(result.status, ObservationValidationResult::Status::ValidMove);
    EXPECT_EQ(chess::FenGenerator::generate(board),
        "rnbqkb1r/pppppppp/5n2/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 9 24");
    const chess::Board committed = board;
    const auto repeated = interpretObservation(board, previous, current);
    EXPECT_EQ(repeated.status, ObservationValidationResult::Status::AmbiguousObservation);
    EXPECT_EQ(board, committed);
}

TEST(ObservationInterpreterTest, RejectsUnconfirmedPromotionsWithAndWithoutCapture) {
    for (const auto color : {chess::PieceColor::White, chess::PieceColor::Black}) {
        for (const bool capture : {false, true}) {
            SCOPED_TRACE(static_cast<int>(color));
            SCOPED_TRACE(capture);
            chess::Board board;
            board.clear();
            board.setPiece({7, 4}, {chess::PieceType::King, chess::PieceColor::White});
            board.setPiece({0, 4}, {chess::PieceType::King, chess::PieceColor::Black});
            board.setSideToMove(color);
            const int sourceRow = color == chess::PieceColor::White ? 1 : 6;
            const int targetRow = color == chess::PieceColor::White ? 0 : 7;
            const int targetCol = capture ? 1 : 0;
            board.setPiece({sourceRow, 0}, {chess::PieceType::Pawn, color});
            if (capture) {
                const auto opponent = color == chess::PieceColor::White
                    ? chess::PieceColor::Black : chess::PieceColor::White;
                board.setPiece({targetRow, targetCol}, {chess::PieceType::Rook, opponent});
            }
            const chess::Board original = board;
            const auto previous = observationFromBoard(board);
            auto current = previous;
            current.cells[sourceRow][0] = CellObservationState::EMPTY;
            current.cells[targetRow][targetCol] = color == chess::PieceColor::White
                ? CellObservationState::WHITE : CellObservationState::BLACK;
            const auto result = interpretObservation(board, previous, current);
            EXPECT_EQ(result.status, ObservationValidationResult::Status::IllegalMove);
            EXPECT_FALSE(result.move.has_value());
            EXPECT_EQ(board, original);
            const auto evaluation = evaluateObservation(board, previous, current);
            EXPECT_EQ(evaluation.result.status, ObservationValidationResult::Status::IllegalMove);
            EXPECT_FALSE(evaluation.candidateBoard.has_value());
            EXPECT_EQ(board, original);
        }
    }
}

TEST(ObservationInterpreterTest, EvaluatesCandidateWithoutChangingAnyInput) {
    const chess::Board board;
    const auto previous = observationFromBoard(board);
    auto current = previous;
    current.cells[6][4] = CellObservationState::EMPTY;
    current.cells[4][4] = CellObservationState::WHITE;
    const auto originalCurrent = current;
    const auto fen = chess::FenGenerator::generate(board);

    const auto evaluation = evaluateObservation(board, previous, current);
    ASSERT_EQ(evaluation.result.status, ObservationValidationResult::Status::ValidMove);
    ASSERT_TRUE(evaluation.result.move.has_value());
    ASSERT_TRUE(evaluation.candidateBoard.has_value());
    EXPECT_EQ(chess::FenGenerator::generate(board), fen);
    EXPECT_EQ(previous.cells, observationFromBoard(board).cells);
    EXPECT_EQ(current.cells, originalCurrent.cells);
    EXPECT_EQ(observationFromBoard(*evaluation.candidateBoard).cells, current.cells);
    EXPECT_EQ(chess::FenGenerator::generate(*evaluation.candidateBoard),
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1");

    chess::Board committed = board;
    const auto result = interpretObservation(committed, previous, current);
    EXPECT_EQ(result.status, evaluation.result.status);
    EXPECT_EQ(result.move, evaluation.result.move);
    EXPECT_EQ(committed, *evaluation.candidateBoard);
}

TEST(ObservationInterpreterTest, EvaluationReturnsNoCandidateForNoChangeOrFailure) {
    const chess::Board board;
    const auto previous = observationFromBoard(board);
    const auto fen = chess::FenGenerator::generate(board);
    const auto unchanged = evaluateObservation(board, previous, previous);
    EXPECT_EQ(unchanged.result.status, ObservationValidationResult::Status::NoChange);
    EXPECT_FALSE(unchanged.result.move.has_value());
    EXPECT_FALSE(unchanged.candidateBoard.has_value());

    auto illegal = previous;
    illegal.cells[6][4] = CellObservationState::EMPTY;
    illegal.cells[3][4] = CellObservationState::WHITE;
    const auto rejected = evaluateObservation(board, previous, illegal);
    EXPECT_EQ(rejected.result.status, ObservationValidationResult::Status::IllegalMove);
    EXPECT_FALSE(rejected.result.move.has_value());
    EXPECT_FALSE(rejected.candidateBoard.has_value());

    auto inconsistent = previous;
    inconsistent.cells[0][0] = CellObservationState::EMPTY;
    const auto ambiguous = evaluateObservation(board, inconsistent, inconsistent);
    EXPECT_EQ(ambiguous.result.status, ObservationValidationResult::Status::AmbiguousObservation);
    EXPECT_FALSE(ambiguous.result.move.has_value());
    EXPECT_FALSE(ambiguous.candidateBoard.has_value());
    EXPECT_EQ(chess::FenGenerator::generate(board), fen);
}

namespace {

chess::Board promotionPosition(chess::PieceColor color, bool capture) {
    chess::Board board;
    board.clear();
    board.setPiece({7, 4}, {chess::PieceType::King, chess::PieceColor::White});
    board.setPiece({0, 4}, {chess::PieceType::King, chess::PieceColor::Black});
    board.setSideToMove(color);
    const bool white = color == chess::PieceColor::White;
    board.setPiece({white ? 1 : 6, capture ? 1 : 0}, {chess::PieceType::Pawn, color});
    if (capture) {
        board.setPiece({white ? 0 : 7, 0}, {chess::PieceType::Rook,
            white ? chess::PieceColor::Black : chess::PieceColor::White});
    }
    board.setEnPassantTarget(chess::Square{white ? 2 : 5, 3});
    board.setHalfmoveClock(9);
    board.setFullmoveNumber(23);
    return board;
}

BoardObservation observeConfirmedMove(const chess::Board& board, const PromotionConfirmation& confirmation) {
    auto observation = observationFromBoard(board);
    observation.cells[confirmation.from.row][confirmation.from.col] = CellObservationState::EMPTY;
    observation.cells[confirmation.to.row][confirmation.to.col] = board.sideToMove() == chess::PieceColor::White
        ? CellObservationState::WHITE : CellObservationState::BLACK;
    return observation;
}

void expectRejectedConfirmation(const chess::Board& original,
    const BoardObservation& previous, const BoardObservation& current,
    const PromotionConfirmation& confirmation) {
    const auto evaluation = evaluateObservation(original, previous, current, confirmation);
    EXPECT_NE(evaluation.result.status, ObservationValidationResult::Status::ValidMove);
    EXPECT_FALSE(evaluation.result.move.has_value());
    EXPECT_FALSE(evaluation.candidateBoard.has_value());
    auto board = original;
    const auto result = interpretObservation(board, previous, current, confirmation);
    EXPECT_EQ(result.status, evaluation.result.status);
    EXPECT_EQ(board, original);
    EXPECT_EQ(chess::FenGenerator::generate(board), chess::FenGenerator::generate(original));
}

} // namespace

TEST(ConfirmedPromotionTest, SupportsEveryPieceColorAndCaptureWithoutDoubleApplication) {
    struct Replacement {
        chess::PieceType type;
        char whiteFen;
        char blackFen;
    };
    const Replacement replacements[] = {
        {chess::PieceType::Queen, 'Q', 'q'}, {chess::PieceType::Rook, 'R', 'r'},
        {chess::PieceType::Bishop, 'B', 'b'}, {chess::PieceType::Knight, 'N', 'n'}
    };
    for (const auto color : {chess::PieceColor::White, chess::PieceColor::Black}) {
        for (const bool capture : {false, true}) {
            for (const auto replacement : replacements) {
                SCOPED_TRACE(static_cast<int>(color));
                SCOPED_TRACE(capture);
                SCOPED_TRACE(static_cast<int>(replacement.type));
                const bool white = color == chess::PieceColor::White;
                auto board = promotionPosition(color, capture);
                const auto original = board;
                const PromotionConfirmation confirmation{
                    {white ? 1 : 6, capture ? 1 : 0}, {white ? 0 : 7, 0}, replacement.type};
                const auto previous = observationFromBoard(board);
                const auto current = observeConfirmedMove(board, confirmation);

                const auto evaluation = evaluateObservation(board, previous, current, confirmation);
                ASSERT_EQ(evaluation.result.status, ObservationValidationResult::Status::ValidMove);
                ASSERT_TRUE(evaluation.result.move.has_value());
                ASSERT_TRUE(evaluation.candidateBoard.has_value());
                EXPECT_EQ(board, original);
                EXPECT_EQ(evaluation.result.move->promotion, replacement.type);
                EXPECT_EQ(evaluation.result.move->capture, capture);
                EXPECT_EQ(observationFromBoard(*evaluation.candidateBoard).cells, current.cells);
                const std::string expectedFen = white
                    ? std::string(1, replacement.whiteFen) + "3k3/8/8/8/8/8/8/4K3 b "
                        + (capture ? "KQk" : "KQkq") + " - 0 23"
                    : "4k3/8/8/8/8/8/8/" + std::string(1, replacement.blackFen) + "3K3 w "
                        + (capture ? "Kkq" : "KQkq") + " - 0 24";
                EXPECT_EQ(chess::FenGenerator::generate(*evaluation.candidateBoard), expectedFen);

                EXPECT_EQ(interpretObservation(board, previous, current).status,
                    ObservationValidationResult::Status::IllegalMove);
                EXPECT_EQ(board, original);
                EXPECT_EQ(interpretObservation(board, previous, current, confirmation).status,
                    ObservationValidationResult::Status::ValidMove);
                EXPECT_EQ(board, *evaluation.candidateBoard);
                EXPECT_EQ(chess::FenGenerator::generate(board), expectedFen);
                const auto committed = board;
                expectRejectedConfirmation(committed, previous, current, confirmation);
            }
        }
    }
}

TEST(ConfirmedPromotionTest, RejectsInvalidReplacementTypes) {
    const auto board = promotionPosition(chess::PieceColor::White, false);
    const auto previous = observationFromBoard(board);
    for (const auto type : {chess::PieceType::None, chess::PieceType::Pawn, chess::PieceType::King}) {
        SCOPED_TRACE(static_cast<int>(type));
        const PromotionConfirmation confirmation{{1, 0}, {0, 0}, type};
        expectRejectedConfirmation(board, previous, observeConfirmedMove(board, confirmation), confirmation);
    }
}

TEST(ConfirmedPromotionTest, RejectsIllegalMovesAndNonPawnSources) {
    struct InvalidMove {
        chess::PieceType sourceType;
        chess::Square from;
        chess::Square to;
        chess::PieceType replacement;
    };
    const InvalidMove cases[] = {
        {chess::PieceType::Pawn, {2, 0}, {1, 0}, chess::PieceType::Queen}, // Not the last rank.
        {chess::PieceType::Pawn, {2, 0}, {0, 0}, chess::PieceType::Queen}, // Illegal double advance.
        {chess::PieceType::Pawn, {1, 1}, {0, 0}, chess::PieceType::Queen}, // Diagonal without capture.
        {chess::PieceType::Queen, {1, 0}, {0, 0}, chess::PieceType::Queen}, // Same type is not promotion.
        {chess::PieceType::Rook, {1, 0}, {0, 0}, chess::PieceType::Queen} // Cannot replace a rook.
    };
    for (const auto test : cases) {
        SCOPED_TRACE(static_cast<int>(test.sourceType));
        SCOPED_TRACE(test.from.row);
        auto board = promotionPosition(chess::PieceColor::White, false);
        board.setPiece({1, 0}, {});
        board.setPiece(test.from, {test.sourceType, chess::PieceColor::White});
        const PromotionConfirmation confirmation{test.from, test.to, test.replacement};
        expectRejectedConfirmation(board, observationFromBoard(board),
            observeConfirmedMove(board, confirmation), confirmation);
    }
}

TEST(ConfirmedPromotionTest, RejectsConfirmationForDifferentMoveOrNoMove) {
    const auto board = promotionPosition(chess::PieceColor::White, false);
    const auto previous = observationFromBoard(board);
    const PromotionConfirmation actual{{1, 0}, {0, 0}, chess::PieceType::Queen};
    const auto current = observeConfirmedMove(board, actual);
    for (const auto confirmation : {
        PromotionConfirmation{{1, 1}, {0, 0}, chess::PieceType::Queen},
        PromotionConfirmation{{1, 0}, {0, 1}, chess::PieceType::Queen},
        PromotionConfirmation{{-1, 0}, {8, 0}, chess::PieceType::Queen}}) {
        expectRejectedConfirmation(board, previous, current, confirmation);
    }
    expectRejectedConfirmation(board, previous, previous, actual);
}

TEST(ConfirmedPromotionTest, RejectsInconsistentBaselineAndExtraVisualChanges) {
    const auto board = promotionPosition(chess::PieceColor::White, false);
    const PromotionConfirmation confirmation{{1, 0}, {0, 0}, chess::PieceType::Queen};
    const auto previous = observationFromBoard(board);
    const auto current = observeConfirmedMove(board, confirmation);
    auto inconsistent = previous;
    inconsistent.cells[4][4] = CellObservationState::WHITE;
    auto extra = current;
    extra.cells[4][4] = CellObservationState::WHITE;
    expectRejectedConfirmation(board, inconsistent, extra, confirmation);
    expectRejectedConfirmation(board, previous, extra, confirmation);
}
