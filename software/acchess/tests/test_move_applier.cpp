#include <gtest/gtest.h>

#include "board/board.hpp"
#include "board/move_applier.hpp"
#include <cstdint>

namespace ac::chess {
namespace {

TEST(MoveApplierTest, AppliesNormalMoveWithoutChangingOtherSquares)
{
    Board board;
    board.clear();

    const Square source{6, 4};
    const Square target{4, 4};
    const Piece pawn{PieceType::Pawn, PieceColor::White};
    const Piece knight{PieceType::Knight, PieceColor::Black};

    board.setPiece(source, pawn);

    MoveApplier::apply(board, Move{.from = source, .to = target});

    EXPECT_TRUE(board.isSqrEmpty(source));
    EXPECT_EQ(board.pieceAt(target), pawn);

    for (uint8_t row = 0; row< 8; ++row){
        for (uint8_t col = 0; col < 8; ++col){
            Square sq{row, col};
            if (sq != source && sq != target){
                EXPECT_TRUE(board.isSqrEmpty(sq));
            }
        }
    }
}

TEST(MoveApplierTest, AppliesCaptureByReplacingTheTargetPiece)
{
    Board board;
    board.clear();

    const Square source{4, 4};
    const Square target{3, 5};
    const Piece whitePawn{PieceType::Pawn, PieceColor::White};

    board.setPiece(source, whitePawn);
    board.setPiece(target, {PieceType::Pawn, PieceColor::Black});

    MoveApplier::apply(board, Move{.from = source, .to = target, .capture = true});

    EXPECT_TRUE(board.isSqrEmpty(source));
    EXPECT_EQ(board.pieceAt(target), whitePawn);
}

TEST(MoveApplierTest, AppliesPromotionAndPreservesPieceColor)
{
    Board board;
    board.clear();
    board.setPiece({1, 0}, {PieceType::Pawn, PieceColor::White});

    MoveApplier::apply(board, Move{.from = {1, 0}, .to = {0, 0}, .promotion = PieceType::Queen});

    EXPECT_EQ(board.pieceAt({0, 0}), (Piece{PieceType::Queen, PieceColor::White}));
}

TEST(MoveApplierTest, AppliesKingSideCastling)
{
    Board board;
    board.clear();
    board.setPiece({7, 4}, {PieceType::King, PieceColor::White});
    board.setPiece({7, 7}, {PieceType::Rook, PieceColor::White});

    MoveApplier::apply(board, Move{.from = {7, 4}, .to = {7, 6}, .castle = true});

    EXPECT_TRUE(board.isSqrEmpty({7, 4}));
    EXPECT_TRUE(board.isSqrEmpty({7, 7}));
    EXPECT_EQ(board.pieceAt({7, 6}), (Piece{PieceType::King, PieceColor::White}));
    EXPECT_EQ(board.pieceAt({7, 5}), (Piece{PieceType::Rook, PieceColor::White}));
}

TEST(MoveApplierTest, AppliesQueenSideCastling)
{
    Board board;
    board.clear();
    board.setPiece({0, 4}, {PieceType::King, PieceColor::Black});
    board.setPiece({0, 0}, {PieceType::Rook, PieceColor::Black});

    MoveApplier::apply(board, Move{.from = {0, 4}, .to = {0, 2}, .castle = true});

    EXPECT_TRUE(board.isSqrEmpty({0, 4}));
    EXPECT_TRUE(board.isSqrEmpty({0, 0}));
    EXPECT_EQ(board.pieceAt({0, 2}), (Piece{PieceType::King, PieceColor::Black}));
    EXPECT_EQ(board.pieceAt({0, 3}), (Piece{PieceType::Rook, PieceColor::Black}));
}

TEST(MoveApplierTest, AppliesEnPassantCapture)
{
    Board board;
    board.clear();
    board.setPiece({3, 4}, {PieceType::Pawn, PieceColor::White});
    board.setPiece({3, 5}, {PieceType::Pawn, PieceColor::Black});

    MoveApplier::apply(board, Move{.from = {3, 4}, .to = {2, 5}, .capture = true, .enPassant = true});

    EXPECT_TRUE(board.isSqrEmpty({3, 4}));
    EXPECT_TRUE(board.isSqrEmpty({3, 5}));
    EXPECT_EQ(board.pieceAt({2, 5}), (Piece{PieceType::Pawn, PieceColor::White}));
}

} // namespace
} // namespace ac::chess
