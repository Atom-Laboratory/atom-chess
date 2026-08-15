#include <gtest/gtest.h>
#include <string>

#include "board/board.hpp"
#include "fen_generator/fen_generator.hpp"

namespace ac::chess {
namespace {

TEST(FenGeneratorTest, GeneratesFenWithPieceTypesAndColors)
{
    Board board;
    board.clear();
    board.setPiece({0, 0}, {PieceType::King, PieceColor::Black});
    board.setPiece({0, 1}, {PieceType::Queen, PieceColor::Black});
    board.setPiece({7, 6}, {PieceType::Knight, PieceColor::White});
    board.setPiece({7, 7}, {PieceType::Rook, PieceColor::White});

    const std::string fen = FenGenerator::generate(board);

    EXPECT_EQ(fen, "kq6/8/8/8/8/8/8/6NR w - - 0 1");
}

TEST(FenGeneratorTest, CompressesEmptySquares)
{
    Board board;
    board.clear();

    const std::string fen = FenGenerator::generate(board);

    EXPECT_EQ(fen, "8/8/8/8/8/8/8/8 w - - 0 1");
}

} // namespace
} // namespace ac::chess
