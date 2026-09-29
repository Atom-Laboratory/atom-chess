#include <gtest/gtest.h>

#include "board/board.hpp"
#include "integration/observation_interpreter.hpp"

namespace ac::integration {
namespace {

ac::BoardObservation observe(const ac::chess::Board& board)
{
    ac::BoardObservation observation;

    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            const auto piece = board.pieceAt({row, col});
            if (piece.type == ac::chess::PieceType::None) {
                observation.cells[row][col] = ac::CellObservationState::EMPTY;
            } else {
                observation.cells[row][col] =
                    piece.color == ac::chess::PieceColor::White
                        ? ac::CellObservationState::WHITE
                        : ac::CellObservationState::BLACK;
            }
        }
    }

    return observation;
}

TEST(ObservationInterpreterTest, ReportsNoChange)
{
    ac::chess::Board board;

    const auto result = ObservationInterpreter::interpret(board, observe(board));

    EXPECT_EQ(result.status, ObservationStatus::NoChange);
    EXPECT_FALSE(result.move.has_value());
}

TEST(ObservationInterpreterTest, InfersNormalPawnMove)
{
    ac::chess::Board board;
    auto observation = observe(board);

    observation.cells[6][4] = ac::CellObservationState::EMPTY;
    observation.cells[4][4] = ac::CellObservationState::WHITE;

    const auto result = ObservationInterpreter::interpret(board, observation);

    ASSERT_EQ(result.status, ObservationStatus::ValidMove);
    ASSERT_TRUE(result.move.has_value());
    EXPECT_EQ(result.move->from, (ac::chess::Square{6, 4}));
    EXPECT_EQ(result.move->to, (ac::chess::Square{4, 4}));
}

TEST(ObservationInterpreterTest, UsesAuthoritativeEnPassantMetadata)
{
    ac::chess::Board board;
    board.clear();
    board.setPiece({7, 4}, {ac::chess::PieceType::King, ac::chess::PieceColor::White});
    board.setPiece({0, 4}, {ac::chess::PieceType::King, ac::chess::PieceColor::Black});
    board.setPiece({3, 4}, {ac::chess::PieceType::Pawn, ac::chess::PieceColor::White});
    board.setPiece({3, 5}, {ac::chess::PieceType::Pawn, ac::chess::PieceColor::Black});
    board.setEnPassantTarget(ac::chess::Square{2, 5});

    auto observation = observe(board);
    observation.cells[3][4] = ac::CellObservationState::EMPTY;
    observation.cells[3][5] = ac::CellObservationState::EMPTY;
    observation.cells[2][5] = ac::CellObservationState::WHITE;

    const auto result = ObservationInterpreter::interpret(board, observation);

    ASSERT_EQ(result.status, ObservationStatus::ValidMove);
    ASSERT_TRUE(result.move.has_value());
    EXPECT_TRUE(result.move->enPassant);
}

TEST(ObservationInterpreterTest, InfersCastlingWithoutMovingOfficialBoard)
{
    ac::chess::Board board;
    board.clear();
    board.setPiece({7, 4}, {ac::chess::PieceType::King, ac::chess::PieceColor::White});
    board.setPiece({7, 7}, {ac::chess::PieceType::Rook, ac::chess::PieceColor::White});
    board.setPiece({0, 4}, {ac::chess::PieceType::King, ac::chess::PieceColor::Black});

    auto observation = observe(board);
    observation.cells[7][4] = ac::CellObservationState::EMPTY;
    observation.cells[7][7] = ac::CellObservationState::EMPTY;
    observation.cells[7][6] = ac::CellObservationState::WHITE;
    observation.cells[7][5] = ac::CellObservationState::WHITE;

    const auto result = ObservationInterpreter::interpret(board, observation);

    ASSERT_EQ(result.status, ObservationStatus::ValidMove);
    ASSERT_TRUE(result.move.has_value());
    EXPECT_TRUE(result.move->castle);
    EXPECT_EQ(board.pieceAt({7, 4}).type, ac::chess::PieceType::King);
    EXPECT_EQ(board.pieceAt({7, 7}).type, ac::chess::PieceType::Rook);
}

TEST(ObservationInterpreterTest, RequiresExplicitPromotionChoice)
{
    ac::chess::Board board;
    board.clear();
    board.setPiece({7, 4}, {ac::chess::PieceType::King, ac::chess::PieceColor::White});
    board.setPiece({0, 4}, {ac::chess::PieceType::King, ac::chess::PieceColor::Black});
    board.setPiece({1, 0}, {ac::chess::PieceType::Pawn, ac::chess::PieceColor::White});

    auto observation = observe(board);
    observation.cells[1][0] = ac::CellObservationState::EMPTY;
    observation.cells[0][0] = ac::CellObservationState::WHITE;

    const auto result = ObservationInterpreter::interpret(board, observation);

    EXPECT_EQ(result.status, ObservationStatus::PromotionRequired);
    EXPECT_FALSE(result.move.has_value());
}

} // namespace
} // namespace ac::integration
