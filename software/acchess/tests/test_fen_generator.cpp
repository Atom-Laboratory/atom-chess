#include <gtest/gtest.h>

#include "board/board.hpp"
#include "fen_generator/fen_generator.hpp"

namespace ac::chess {
namespace {

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
