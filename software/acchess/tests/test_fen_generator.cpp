#include <gtest/gtest.h>

#include "board/board.hpp"
#include "fen_generator/fen_generator.hpp"

namespace ac::chess {
namespace {

TEST(FenGeneratorTest, GeneratesArbitraryPositionWithPieceTypesAndColors)
{
    Board board;
    board.clear();
    board.setPiece({0, 0}, {PieceType::King, PieceColor::Black});
    board.setPiece({0, 1}, {PieceType::Queen, PieceColor::Black});
    board.setPiece({7, 6}, {PieceType::Knight, PieceColor::White});
    board.setPiece({7, 7}, {PieceType::Rook, PieceColor::White});

    EXPECT_EQ(
        FenGenerator::generate(board),
        "kq6/8/8/8/8/8/8/6NR w - - 0 1"
    );
}

TEST(FenGeneratorTest, GeneratesInitialPositionWithAllPieceTypesAndColors)
{
    Board board;

    EXPECT_EQ(
        FenGenerator::generate(board),
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
    );
}

TEST(FenGeneratorTest, CompressesEmptySquares)
{
    Board board;
    board.clear();

    EXPECT_EQ(
        FenGenerator::generate(board),
        "8/8/8/8/8/8/8/8 w - - 0 1"
    );
}

} // namespace
} // namespace ac::chess
