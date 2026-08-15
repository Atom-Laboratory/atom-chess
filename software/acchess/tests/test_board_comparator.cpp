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

    ASSERT_EQ(changes.size(), 2u);
    EXPECT_EQ(changes[0], (SquareChange{
        .square = {1, 4},
        .before = {PieceType::Pawn, PieceColor::White},
        .after = {}
    }));
    EXPECT_EQ(changes[1], (SquareChange{
        .square = {3, 4},
        .before = {},
        .after = {PieceType::Pawn, PieceColor::White}
    }));
}

TEST(BoardComparatorTest, ReportsCapture)
{
    Board previous;
    previous.clear();
    previous.setPiece({4, 4}, {PieceType::Pawn, PieceColor::White});
    previous.setPiece({3, 5}, {PieceType::Pawn, PieceColor::Black});

    Board current = previous;
    current.setPiece({4, 4}, Piece{});
    current.setPiece({3, 5}, {PieceType::Pawn, PieceColor::White});

    const auto changes = BoardComparator::compare(previous, current);

    ASSERT_EQ(changes.size(), 2u);
    EXPECT_EQ(changes[0].square, (Square{3, 5}));
    EXPECT_EQ(changes[0].before, (Piece{PieceType::Pawn, PieceColor::Black}));
    EXPECT_EQ(changes[0].after, (Piece{PieceType::Pawn, PieceColor::White}));
    EXPECT_EQ(changes[1].square, (Square{4, 4}));
}

TEST(BoardComparatorTest, ReportsPromotion)
{
    Board previous;
    previous.clear();
    previous.setPiece({1, 0}, {PieceType::Pawn, PieceColor::White});

    Board current = previous;
    current.setPiece({1, 0}, Piece{});
    current.setPiece({0, 0}, {PieceType::Queen, PieceColor::White});

    const auto changes = BoardComparator::compare(previous, current);

    ASSERT_EQ(changes.size(), 2u);
    EXPECT_EQ(changes[0].square, (Square{0, 0}));
    EXPECT_EQ(changes[0].after, (Piece{PieceType::Queen, PieceColor::White}));
}

TEST(BoardComparatorTest, ReportsKingSideCastling)
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

    EXPECT_EQ(BoardComparator::compare(previous, current).size(), 4u);
}

TEST(BoardComparatorTest, ReportsQueenSideCastling)
{
    Board previous;
    previous.clear();
    previous.setPiece({0, 4}, {PieceType::King, PieceColor::Black});
    previous.setPiece({0, 0}, {PieceType::Rook, PieceColor::Black});

    Board current = previous;
    current.setPiece({0, 4}, Piece{});
    current.setPiece({0, 2}, {PieceType::King, PieceColor::Black});
    current.setPiece({0, 0}, Piece{});
    current.setPiece({0, 3}, {PieceType::Rook, PieceColor::Black});

    EXPECT_EQ(BoardComparator::compare(previous, current).size(), 4u);
}

TEST(BoardComparatorTest, ReportsEnPassant)
{
    Board previous;
    previous.clear();
    previous.setPiece({3, 4}, {PieceType::Pawn, PieceColor::White});
    previous.setPiece({3, 5}, {PieceType::Pawn, PieceColor::Black});

    Board current = previous;
    current.setPiece({3, 4}, Piece{});
    current.setPiece({3, 5}, Piece{});
    current.setPiece({2, 5}, {PieceType::Pawn, PieceColor::White});

    EXPECT_EQ(BoardComparator::compare(previous, current).size(), 3u);
}

TEST(BoardComparatorTest, ReportsAll64ChangesWithoutInterpretingThem)
{
    Board previous;
    previous.clear();
    Board current;
    current.clear();

    for (std::uint8_t row = 0; row < 8; ++row) {
        for (std::uint8_t column = 0; column < 8; ++column) {
            current.setPiece(
                {row, column},
                {PieceType::Pawn, PieceColor::White}
            );
        }
    }

    const auto changes = BoardComparator::compare(previous, current);

    ASSERT_EQ(changes.size(), 64u);
    EXPECT_EQ(changes.front().square, (Square{0, 0}));
    EXPECT_EQ(changes.back().square, (Square{7, 7}));
}

} // namespace
} // namespace ac::chess
