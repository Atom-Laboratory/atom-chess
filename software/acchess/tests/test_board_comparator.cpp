#include <gtest/gtest.h>

#include "board/board.hpp"
#include "board/board_comparator.hpp"
#include <cstdint>

namespace ac::chess {
namespace {

TEST(BoardComparatorTest, ReturnsNoChangesForEqualBoards)
{
    Board previous;
    Board current;

    EXPECT_TRUE(BoardComparator::compare(previous, current).empty());
}

TEST(BoardComparatorTest, ReportsSimpleMoveInRowMajorOrder)
{
    Board previous;
    previous.clear();
    previous.setPiece({1, 4}, {PieceType::Pawn, PieceColor::White});

    Board current = previous;
    current.setPiece({1, 4}, Piece{});
    current.setPiece({3, 4}, {PieceType::Pawn, PieceColor::White});

    const auto changes = BoardComparator::compare(previous, current);

    ASSERT_EQ(changes.size(), 2);
    EXPECT_EQ(
        changes[0], 
        (SquareChange{
            .square = {1, 4}, 
            .before = {PieceType::Pawn, PieceColor::White}, 
            .after = {}
        }));
    
    EXPECT_EQ(
        changes[1], 
        (SquareChange{
            .square = {3, 4}, 
            .before = {}, 
            .after = {PieceType::Pawn, PieceColor::White}
        }));
}

TEST(BoardComparatorTest, ReportsCaptureWithPreviousAndCurrentPieces)
{
    Board previous;
    previous.clear();
    previous.setPiece({4, 4}, {PieceType::Pawn, PieceColor::White});
    previous.setPiece({3, 5}, {PieceType::Pawn, PieceColor::Black});

    Board current = previous;
    current.setPiece({4, 4}, Piece{});
    current.setPiece({3, 5}, {PieceType::Pawn, PieceColor::White});

    const auto changes = BoardComparator::compare(previous, current);

    ASSERT_EQ(changes.size(), 2);
    EXPECT_EQ(changes[0].square, (Square{3, 5}));
    EXPECT_EQ(changes[0].before, (Piece{PieceType::Pawn, PieceColor::Black}));
    EXPECT_EQ(changes[0].after, (Piece{PieceType::Pawn, PieceColor::White}));
}

TEST(BoardComparatorTest, ReportsPromotionAsTwoChangedSquares)
{
    Board previous;
    previous.clear();
    previous.setPiece({1, 0}, {PieceType::Pawn, PieceColor::White});

    Board current = previous;
    current.setPiece({1, 0}, Piece{});
    current.setPiece({0, 0}, {PieceType::Queen, PieceColor::White});

    const auto changes = BoardComparator::compare(previous, current);

    ASSERT_EQ(changes.size(), 2);
    EXPECT_EQ(changes[0].square, (Square{0, 0}));
    EXPECT_EQ(changes[0].after, (Piece{PieceType::Queen, PieceColor::White}));
}

TEST(BoardComparatorTest, ReportsFourChangedSquaresForCastling)
{
    Board previous;
    previous.clear();
    previous.setPiece({7, 4}, {PieceType::King, PieceColor::White});
    previous.setPiece({7, 7}, {PieceType::Rook, PieceColor::White});

    Board current = previous;
    current.setPiece({7, 4}, Piece{});
    current.setPiece({7, 6}, {PieceType::King, PieceColor::White});
    current.setPiece({7, 7}, Piece{});
    current.setPiece({7, 5}, {PieceType::Rook, PieceColor::White});

    EXPECT_EQ(BoardComparator::compare(previous, current).size(), 4);
}

TEST(BoardComparatorTest, ReportsThreeChangedSquaresForEnPassant)
{
    Board previous;
    previous.clear();
    previous.setPiece({3, 4}, {PieceType::Pawn, PieceColor::White});
    previous.setPiece({3, 5}, {PieceType::Pawn, PieceColor::Black});

    Board current = previous;
    current.setPiece({3, 4}, Piece{});
    current.setPiece({3, 5}, Piece{});
    current.setPiece({2, 5}, {PieceType::Pawn, PieceColor::White});

    EXPECT_EQ(BoardComparator::compare(previous, current).size(), 3);
}

TEST(BoardComparatorTest, ReportsAllChangedSquaresWithoutInterpretingThem)
{
    Board previous;
    previous.clear();

    Board current;
    current.clear();

    for (uint8_t row = 0; row < 8; ++row) {
        for (uint8_t col = 0; col < 8; ++col) {
            current.setPiece({row, col}, {PieceType::Pawn, PieceColor::White});
        }
    }

    const auto changes = BoardComparator::compare(previous, current);

    ASSERT_EQ(changes.size(), 64);
    EXPECT_EQ(changes.front().square, (Square{0, 0}));
    EXPECT_EQ(changes.back().square, (Square{7, 7}));
}

} // namespace
} // namespace ac::chess
