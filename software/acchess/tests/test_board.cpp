#include <gtest/gtest.h>

#include "board/board.hpp"
#include "fen_generator/fen_generator.hpp"

#include <cstdint>
#include <stdexcept>

namespace ac::chess {
namespace {

/**
 * @brief Verifies the initial layout and that clear() empties all 64 squares.
 */
TEST(BoardTest, StartsInInitialPositionAndCanBeCleared)
{
    Board board;

    EXPECT_EQ(board.pieceAt({0, 0}), (Piece{PieceType::Rook, PieceColor::Black}));
    EXPECT_EQ(board.pieceAt({7, 4}), (Piece{PieceType::King, PieceColor::White}));

    board.clear();

    for (std::uint8_t row = 0; row < 8; ++row) {
        for (std::uint8_t column = 0; column < 8; ++column) {
            EXPECT_TRUE(board.isSqrEmpty({row, column}));
        }
    }
}

TEST(BoardTest, ResetRestoresInitialPosition)
{
    Board board;
    board.clear();

    board.reset();

    EXPECT_EQ(board.pieceAt({0, 4}), (Piece{PieceType::King, PieceColor::Black}));
    EXPECT_EQ(board.pieceAt({6, 3}), (Piece{PieceType::Pawn, PieceColor::White}));
}

/**
 * @brief Verifies that piece updates affect only the selected square.
 */
TEST(BoardTest, InsertsReplacesAndRemovesOnlyTheSelectedPiece)
{
    Board board;
    board.clear();
    const Square target{4, 4};

    board.setPiece(target, {PieceType::Knight, PieceColor::White});

    for (std::uint8_t row = 0; row < 8; ++row) {
        for (std::uint8_t column = 0; column < 8; ++column) {
            const Square square{row, column};
            if (square == target) {
                EXPECT_EQ(
                    board.pieceAt(square),
                    (Piece{PieceType::Knight, PieceColor::White})
                );
            } else {
                EXPECT_TRUE(board.isSqrEmpty(square));
            }
        }
    }

    board.setPiece(target, {PieceType::Queen, PieceColor::Black});
    EXPECT_EQ(
        board.pieceAt(target),
        (Piece{PieceType::Queen, PieceColor::Black})
    );

    board.setPiece(target, Piece{});
    EXPECT_TRUE(board.isSqrEmpty(target));
}

TEST(BoardTest, RejectsInvalidPieceEncodingsWithoutChangingTheBoard)
{
    Board board;
    const Square target{4, 4};
    const Piece original = board.pieceAt(target);

    EXPECT_THROW(
        board.setPiece(target, {PieceType::None, PieceColor::White}),
        std::invalid_argument
    );
    EXPECT_EQ(board.pieceAt(target), original);

    EXPECT_THROW(
        board.setPiece(target, {PieceType::Pawn, PieceColor::None}),
        std::invalid_argument
    );
    EXPECT_EQ(board.pieceAt(target), original);
}

TEST(PieceTest, ValidatesTypeAndColorAsOneInvariant)
{
    EXPECT_TRUE(isValid(Piece{}));
    EXPECT_TRUE(isValid({PieceType::Pawn, PieceColor::White}));
    EXPECT_TRUE(isValid({PieceType::King, PieceColor::Black}));
    EXPECT_FALSE(isValid({PieceType::None, PieceColor::White}));
    EXPECT_FALSE(isValid({PieceType::Pawn, PieceColor::None}));
}

TEST(SquareTest, DefaultsToAnInvalidSentinel)
{
    const Square square;

    EXPECT_EQ(square.row, -1);
    EXPECT_EQ(square.col, -1);
}

TEST(MoveTest, DefaultsToInvalidSourceAndDestinationSquares)
{
    const Move move;

    EXPECT_EQ(move.from, Square{});
    EXPECT_EQ(move.to, Square{});
}

TEST(BoardTest, ComparesEqualAndDifferentBoards)
{
    Board first;
    Board second;

    EXPECT_EQ(first, second);
    EXPECT_FALSE(first != second);

    first.setPiece({4, 4}, {PieceType::Pawn, PieceColor::White});
    EXPECT_NE(first, second);

    second.setPiece({4, 4}, {PieceType::Pawn, PieceColor::White});
    EXPECT_EQ(first, second);
}

/**
 * @brief Verifies that invalid coordinates are rejected before board access.
 */
TEST(BoardTest, RejectsSquaresOutsideTheBoard)
{
    Board board;

    EXPECT_THROW(board.pieceAt({-1, 0}), std::out_of_range);
    EXPECT_THROW(board.pieceAt({0, 8}), std::out_of_range);
    EXPECT_THROW(
        board.setPiece({8, 0}, {PieceType::Pawn, PieceColor::White}),
        std::out_of_range
    );
}

/**
 * @brief Verifies that the official Board state is serialized by FenGenerator.
 */
TEST(BoardIntegrationTest, GeneratesFenFromBoard)
{
    Board board;

    EXPECT_EQ(
        FenGenerator::generate(board),
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    );
}

} // namespace
} // namespace ac::chess
