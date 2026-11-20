#include <gtest/gtest.h>

#include <string>

#include "board/board.hpp"
#include "board/move_applier.hpp"
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
        "kq6/8/8/8/8/8/8/6NR w KQkq - 0 1"
    );
}

TEST(FenGeneratorTest, GeneratesInitialPositionWithAllPieceTypesAndColors)
{
    Board board;

    EXPECT_EQ(
        FenGenerator::generate(board),
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    );
}

TEST(FenGeneratorTest, CompressesEmptySquares)
{
    Board board;
    board.clear();

    EXPECT_EQ(
        FenGenerator::generate(board),
        "8/8/8/8/8/8/8/8 w KQkq - 0 1"
    );
}

} // namespace
} // namespace ac::chess


namespace ac::chess {
namespace {

TEST(FenGeneratorTest, SerializesDynamicMetadata)
{
    Board board;
    board.setSideToMove(PieceColor::Black);
    board.setCastlingRights({true, false, false, true});
    board.setEnPassantTarget(Square{5, 4});
    board.setHalfmoveClock(12);
    board.setFullmoveNumber(7);

    EXPECT_EQ(
        FenGenerator::generate(board),
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b Kq e3 12 7"
    );
}


} // namespace
} // namespace ac::chess


// ---------------------------------------------------------------------------
// Issue #64 - FEN serialization after pawn promotion
//
// These tests drive the real Chess Core transition (MoveApplier::apply) and
// then serialize the resulting Board. They cover the promoted piece letter and
// colour, plus the FEN metadata fields a promotion must update.
// ---------------------------------------------------------------------------
namespace ac::chess {
namespace {

constexpr CastlingRights kNoCastlingRights{false, false, false, false};

constexpr Piece kWhiteKing{PieceType::King, PieceColor::White};
constexpr Piece kBlackKing{PieceType::King, PieceColor::Black};
constexpr Piece kWhitePawn{PieceType::Pawn, PieceColor::White};
constexpr Piece kBlackPawn{PieceType::Pawn, PieceColor::Black};

/**
 * @brief Builds a bare board with the given side to move and metadata that
 *        differs from the defaults, so a wrong/unchanged field cannot pass
 *        by coincidence.
 */
Board makeBareBoard(PieceColor sideToMove, int halfmove, int fullmove)
{
    Board board;
    board.clear();
    board.setCastlingRights(kNoCastlingRights);
    board.setSideToMove(sideToMove);
    board.setHalfmoveClock(halfmove);
    board.setFullmoveNumber(fullmove);
    return board;
}

struct PromotionCase {
    const char* name;
    PieceColor color;
    PieceType promotion;
    const char* fenAfter;
};

class FenPromotionTest : public ::testing::TestWithParam<PromotionCase> {};

// White pawn a7 -> a8 (row 1 -> row 0). Black pawn a2 -> a1 (row 6 -> row 7).
// White starts at halfmove 37 / fullmove 40, Black likewise.
TEST_P(FenPromotionTest, SerializesPromotedPieceAndUpdatedMetadata)
{
    const PromotionCase& testCase = GetParam();
    const bool white = testCase.color == PieceColor::White;

    Board board = makeBareBoard(testCase.color, 37, 40);
    Move move;
    if (white) {
        board.setPiece({7, 4}, kWhiteKing);  // e1
        board.setPiece({3, 7}, kBlackKing);  // h5
        board.setPiece({1, 0}, kWhitePawn);  // a7
        move = Move{.from = {1, 0}, .to = {0, 0}, .promotion = testCase.promotion};
    } else {
        board.setPiece({0, 4}, kBlackKing);  // e8
        board.setPiece({4, 7}, kWhiteKing);  // h4
        board.setPiece({6, 0}, kBlackPawn);  // a2
        move = Move{.from = {6, 0}, .to = {7, 0}, .promotion = testCase.promotion};
    }

    // Precondition: the pawn is still a pawn and the clock is untouched.
    const char* fenBefore = white
        ? "8/P7/8/7k/8/8/8/4K3 w - - 37 40"
        : "4k3/8/8/8/7K/8/p7/8 b - - 37 40";
    EXPECT_EQ(FenGenerator::generate(board), fenBefore);

    MoveApplier::apply(board, move);

    EXPECT_EQ(FenGenerator::generate(board), testCase.fenAfter);
}

INSTANTIATE_TEST_SUITE_P(
    AllPromotionPieces,
    FenPromotionTest,
    ::testing::Values(
        // White promotes: uppercase letter, Black to move, fullmove unchanged.
        PromotionCase{"WhiteQueen", PieceColor::White, PieceType::Queen,
                      "Q7/8/8/7k/8/8/8/4K3 b - - 0 40"},
        PromotionCase{"WhiteRook", PieceColor::White, PieceType::Rook,
                      "R7/8/8/7k/8/8/8/4K3 b - - 0 40"},
        PromotionCase{"WhiteBishop", PieceColor::White, PieceType::Bishop,
                      "B7/8/8/7k/8/8/8/4K3 b - - 0 40"},
        PromotionCase{"WhiteKnight", PieceColor::White, PieceType::Knight,
                      "N7/8/8/7k/8/8/8/4K3 b - - 0 40"},
        // Black promotes: lowercase letter, White to move, fullmove + 1.
        PromotionCase{"BlackQueen", PieceColor::Black, PieceType::Queen,
                      "4k3/8/8/8/7K/8/8/q7 w - - 0 41"},
        PromotionCase{"BlackRook", PieceColor::Black, PieceType::Rook,
                      "4k3/8/8/8/7K/8/8/r7 w - - 0 41"},
        PromotionCase{"BlackBishop", PieceColor::Black, PieceType::Bishop,
                      "4k3/8/8/8/7K/8/8/b7 w - - 0 41"},
        PromotionCase{"BlackKnight", PieceColor::Black, PieceType::Knight,
                      "4k3/8/8/8/7K/8/8/n7 w - - 0 41"}),
    [](const ::testing::TestParamInfo<PromotionCase>& info) {
        return std::string{info.param.name};
    });

struct PromotionCaptureCase {
    const char* name;
    Square pawn;
    Square target;
    PieceType promotion;
    const char* fenAfter;
};

class FenPromotionCaptureTest
    : public ::testing::TestWithParam<PromotionCaptureCase> {};

// Capturing a rook on its home square by promotion must drop exactly that
// rook's castling right from the serialized KQkq field.
TEST_P(FenPromotionCaptureTest, SerializesCapturedRookCastlingRevocation)
{
    const PromotionCaptureCase& testCase = GetParam();

    Board board = makeBareBoard(PieceColor::White, 0, 1);
    board.setCastlingRights(CastlingRights{false, false, true, true});
    board.setPiece({7, 4}, kWhiteKing);                              // e1
    board.setPiece({0, 4}, kBlackKing);                              // e8
    board.setPiece({0, 0}, {PieceType::Rook, PieceColor::Black});    // a8
    board.setPiece({0, 7}, {PieceType::Rook, PieceColor::Black});    // h8
    board.setPiece(testCase.pawn, kWhitePawn);

    MoveApplier::apply(board, Move{
        .from = testCase.pawn,
        .to = testCase.target,
        .promotion = testCase.promotion,
        .capture = true
    });

    EXPECT_EQ(FenGenerator::generate(board), testCase.fenAfter);
}

INSTANTIATE_TEST_SUITE_P(
    CapturingBlackRooks,
    FenPromotionCaptureTest,
    ::testing::Values(
        // bxa8=Q removes the queen-side right only -> "k".
        PromotionCaptureCase{"PawnB7TakesA8Queen", {1, 1}, {0, 0}, PieceType::Queen,
                             "Q3k2r/8/8/8/8/8/8/4K3 b k - 0 1"},
        // gxh8=N removes the king-side right only -> "q".
        PromotionCaptureCase{"PawnG7TakesH8Knight", {1, 6}, {0, 7}, PieceType::Knight,
                             "r3k2N/8/8/8/8/8/8/4K3 b q - 0 1"}),
    [](const ::testing::TestParamInfo<PromotionCaptureCase>& info) {
        return std::string{info.param.name};
    });

TEST(FenPromotionTest, PromotionClearsPendingEnPassantTarget)
{
    // Black has just played e7-e5, so the FEN carries e6 until White moves.
    Board board = makeBareBoard(PieceColor::White, 0, 1);
    board.setPiece({7, 4}, kWhiteKing);  // e1
    board.setPiece({3, 7}, kBlackKing);  // h5
    board.setPiece({3, 4}, kBlackPawn);  // e5
    board.setPiece({1, 0}, kWhitePawn);  // a7
    board.setEnPassantTarget(Square{2, 4});

    EXPECT_EQ(
        FenGenerator::generate(board),
        "8/P7/8/4p2k/8/8/8/4K3 w - e6 0 1"
    );

    MoveApplier::apply(board, Move{
        .from = {1, 0}, .to = {0, 0}, .promotion = PieceType::Queen
    });

    // A promotion is a single-step pawn move: the stale target must be gone.
    EXPECT_EQ(
        FenGenerator::generate(board),
        "Q7/8/8/4p2k/8/8/8/4K3 b - - 0 1"
    );
}

TEST(FenPromotionTest, SecondQueenFromPromotionIsSerializedAlongsideFirst)
{
    Board board = makeBareBoard(PieceColor::White, 5, 20);
    board.setPiece({7, 4}, kWhiteKing);                               // e1
    board.setPiece({7, 3}, {PieceType::Queen, PieceColor::White});    // d1
    board.setPiece({3, 7}, kBlackKing);                               // h5
    board.setPiece({1, 0}, kWhitePawn);                               // a7

    MoveApplier::apply(board, Move{
        .from = {1, 0}, .to = {0, 0}, .promotion = PieceType::Queen
    });

    EXPECT_EQ(
        FenGenerator::generate(board),
        "Q7/8/8/7k/8/8/8/3QK3 b - - 0 20"
    );
}

} // namespace
} // namespace ac::chess
