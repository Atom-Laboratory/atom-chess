#include <gtest/gtest.h>

#include "board/board.hpp"
#include "board/board_comparator.hpp"
#include "board/move_applier.hpp"
#include "board/move_validator.hpp"

#include <vector>

namespace ac::chess {
namespace {

Board boardWithKings()
{
    Board board;
    board.clear();
    board.setPiece({7, 4}, {PieceType::King, PieceColor::White});
    board.setPiece({0, 4}, {PieceType::King, PieceColor::Black});
    return board;
}

Board afterMove(const Board& previous, const Move& move)
{
    Board observed = previous;
    MoveApplier::apply(observed, move);
    return observed;
}

TEST(MoveValidatorTest, InfersAValidPawnPush)
{
    Board previous = boardWithKings();
    previous.setPiece({6, 3}, {PieceType::Pawn, PieceColor::White});
    const Move expected{.from = {6, 3}, .to = {4, 3}};

    const auto result = MoveValidator::validate(
        previous,
        afterMove(previous, expected),
        PieceColor::White
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, RejectsBoardWithoutWhiteKing)
{
    Board previous = boardWithKings();
    previous.setPiece({7, 4}, {});
    previous.setPiece({1, 3}, {PieceType::Pawn, PieceColor::Black});
    const Board observed = afterMove(
        previous,
        Move{.from = {1, 3}, .to = {2, 3}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::Black).has_value()
    );
}

TEST(MoveValidatorTest, RejectsBoardWithoutBlackKing)
{
    Board previous = boardWithKings();
    previous.setPiece({0, 4}, {});
    previous.setPiece({6, 3}, {PieceType::Pawn, PieceColor::White});
    const Board observed = afterMove(
        previous,
        Move{.from = {6, 3}, .to = {5, 3}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, RejectsBoardWithTwoWhiteKings)
{
    Board previous = boardWithKings();
    previous.setPiece({7, 0}, {PieceType::King, PieceColor::White});
    previous.setPiece({1, 3}, {PieceType::Pawn, PieceColor::Black});
    const Board observed = afterMove(
        previous,
        Move{.from = {1, 3}, .to = {2, 3}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::Black).has_value()
    );
}

TEST(MoveValidatorTest, RejectsBoardWithTwoBlackKings)
{
    Board previous = boardWithKings();
    previous.setPiece({0, 0}, {PieceType::King, PieceColor::Black});
    previous.setPiece({6, 3}, {PieceType::Pawn, PieceColor::White});
    const Board observed = afterMove(
        previous,
        Move{.from = {6, 3}, .to = {5, 3}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, AcceptsBoardWithExactlyOneKingOfEachColor)
{
    Board previous = boardWithKings();
    previous.setPiece({6, 3}, {PieceType::Pawn, PieceColor::White});
    const Move expected{.from = {6, 3}, .to = {5, 3}};

    const auto result = MoveValidator::validate(
        previous,
        afterMove(previous, expected),
        PieceColor::White
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, RejectsAMoveFromTheWrongSide)
{
    Board previous = boardWithKings();
    previous.setPiece({6, 3}, {PieceType::Pawn, PieceColor::White});
    const Board observed = afterMove(
        previous,
        Move{.from = {6, 3}, .to = {5, 3}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::Black).has_value()
    );
}

TEST(MoveValidatorTest, ValidatesKnightMovement)
{
    Board previous = boardWithKings();
    previous.setPiece({4, 4}, {PieceType::Knight, PieceColor::White});
    const Move expected{.from = {4, 4}, .to = {2, 5}};

    const auto result = MoveValidator::validate(
        previous,
        afterMove(previous, expected),
        PieceColor::White
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, ValidatesBishopRookQueenAndKingMovement)
{
    struct TestCase {
        PieceType type;
        Square from;
        Square to;
    };

    const std::vector<TestCase> testCases{
        {PieceType::Bishop, {4, 4}, {2, 6}},
        {PieceType::Rook, {4, 4}, {4, 7}},
        {PieceType::Queen, {4, 4}, {1, 1}},
        {PieceType::King, {7, 4}, {6, 4}}
    };

    for (const TestCase& testCase : testCases) {
        SCOPED_TRACE(static_cast<int>(testCase.type));

        Board previous = boardWithKings();
        previous.setPiece(
            testCase.from,
            {testCase.type, PieceColor::White}
        );
        const Move expected{
            .from = testCase.from,
            .to = testCase.to
        };

        const auto result = MoveValidator::validate(
            previous,
            afterMove(previous, expected),
            PieceColor::White
        );

        ASSERT_TRUE(result.has_value());
        EXPECT_EQ(*result, expected);
    }
}

TEST(MoveValidatorTest, RejectsInvalidPieceGeometry)
{
    Board previous = boardWithKings();
    previous.setPiece({4, 4}, {PieceType::Knight, PieceColor::White});
    const Board observed = afterMove(
        previous,
        Move{.from = {4, 4}, .to = {4, 6}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, RejectsBlockedSlidingPieces)
{
    Board previous = boardWithKings();
    previous.setPiece({5, 2}, {PieceType::Bishop, PieceColor::White});
    previous.setPiece({4, 3}, {PieceType::Pawn, PieceColor::White});
    const Board observed = afterMove(
        previous,
        Move{.from = {5, 2}, .to = {2, 5}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, RejectsSameColorDestination)
{
    Board previous = boardWithKings();
    previous.setPiece({4, 0}, {PieceType::Rook, PieceColor::White});
    previous.setPiece({4, 6}, {PieceType::Pawn, PieceColor::White});
    const Board observed = afterMove(
        previous,
        Move{.from = {4, 0}, .to = {4, 6}, .capture = true}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, RejectsBackwardPawnMovement)
{
    Board previous = boardWithKings();
    previous.setPiece({4, 3}, {PieceType::Pawn, PieceColor::White});
    const Board observed = afterMove(
        previous,
        Move{.from = {4, 3}, .to = {5, 3}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, InfersCaptures)
{
    Board previous = boardWithKings();
    previous.setPiece({4, 0}, {PieceType::Rook, PieceColor::White});
    previous.setPiece({4, 6}, {PieceType::Knight, PieceColor::Black});
    const Move expected{
        .from = {4, 0},
        .to = {4, 6},
        .capture = true
    };

    const auto result = MoveValidator::validate(
        previous,
        afterMove(previous, expected),
        PieceColor::White
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, InfersPromotion)
{
    Board previous = boardWithKings();
    previous.setPiece({1, 0}, {PieceType::Pawn, PieceColor::White});
    const Move expected{
        .from = {1, 0},
        .to = {0, 0},
        .promotion = PieceType::Queen
    };

    const auto result = MoveValidator::validate(
        previous,
        afterMove(previous, expected),
        PieceColor::White
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, InfersPromotionCapture)
{
    Board previous = boardWithKings();
    previous.setPiece({1, 0}, {PieceType::Pawn, PieceColor::White});
    previous.setPiece({0, 1}, {PieceType::Rook, PieceColor::Black});
    const Move expected{
        .from = {1, 0},
        .to = {0, 1},
        .promotion = PieceType::Knight,
        .capture = true
    };

    const auto result = MoveValidator::validate(
        previous,
        afterMove(previous, expected),
        PieceColor::White
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, RejectsInvalidPromotionPiece)
{
    Board previous = boardWithKings();
    previous.setPiece({1, 0}, {PieceType::Pawn, PieceColor::White});
    const Board observed = afterMove(
        previous,
        Move{
            .from = {1, 0},
            .to = {0, 0},
            .promotion = PieceType::King
        }
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, InfersKingSideCastling)
{
    Board previous = boardWithKings();
    previous.setPiece({7, 7}, {PieceType::Rook, PieceColor::White});
    const Move expected{
        .from = {7, 4},
        .to = {7, 6},
        .castle = true
    };

    const auto result = MoveValidator::validate(
        previous,
        afterMove(previous, expected),
        PieceColor::White
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, InfersQueenSideCastling)
{
    Board previous = boardWithKings();
    previous.setPiece({7, 0}, {PieceType::Rook, PieceColor::White});
    const Move expected{
        .from = {7, 4},
        .to = {7, 2},
        .castle = true
    };

    const auto result = MoveValidator::validate(
        previous,
        afterMove(previous, expected),
        PieceColor::White
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, RejectsCastlingThroughCheck)
{
    Board previous = boardWithKings();
    previous.setPiece({7, 7}, {PieceType::Rook, PieceColor::White});
    previous.setPiece({0, 5}, {PieceType::Rook, PieceColor::Black});
    const Board observed = afterMove(
        previous,
        Move{.from = {7, 4}, .to = {7, 6}, .castle = true}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, InfersEnPassant)
{
    Board previous = boardWithKings();
    previous.setPiece({3, 4}, {PieceType::Pawn, PieceColor::White});
    previous.setPiece({3, 5}, {PieceType::Pawn, PieceColor::Black});
    const Move expected{
        .from = {3, 4},
        .to = {2, 5},
        .capture = true,
        .enPassant = true
    };

    const auto result = MoveValidator::validate(
        previous,
        afterMove(previous, expected),
        PieceColor::White
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, RejectsMovesThatExposeTheOwnKing)
{
    Board previous;
    previous.clear();
    previous.setPiece({7, 4}, {PieceType::King, PieceColor::White});
    previous.setPiece({0, 0}, {PieceType::King, PieceColor::Black});
    previous.setPiece({0, 4}, {PieceType::Rook, PieceColor::Black});
    previous.setPiece({6, 4}, {PieceType::Rook, PieceColor::White});
    const Board observed = afterMove(
        previous,
        Move{.from = {6, 4}, .to = {6, 5}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, RejectsKingMovementIntoCheck)
{
    Board previous = boardWithKings();
    previous.setPiece({0, 5}, {PieceType::Rook, PieceColor::Black});
    const Board observed = afterMove(
        previous,
        Move{.from = {7, 4}, .to = {6, 5}}
    );

    EXPECT_FALSE(
        MoveValidator::validate(previous, observed, PieceColor::White).has_value()
    );
}

TEST(MoveValidatorTest, AcceptsAChangesSequenceDirectly)
{
    Board previous = boardWithKings();
    previous.setPiece({1, 2}, {PieceType::Pawn, PieceColor::Black});
    const Move expected{.from = {1, 2}, .to = {3, 2}};
    const Board observed = afterMove(previous, expected);
    const auto changes = BoardComparator::compare(previous, observed);

    const auto result = MoveValidator::validate(
        previous,
        changes,
        PieceColor::Black
    );

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

TEST(MoveValidatorTest, RejectsChangesWithAnIncorrectPreviousPiece)
{
    Board previous = boardWithKings();
    const std::vector<SquareChange> changes{
        {
            .square = {6, 0},
            .before = {PieceType::Pawn, PieceColor::White},
            .after = {}
        },
        {
            .square = {5, 0},
            .before = {},
            .after = {PieceType::Pawn, PieceColor::White}
        }
    };

    EXPECT_FALSE(
        MoveValidator::validate(previous, changes, PieceColor::White).has_value()
    );
}

} // namespace
} // namespace ac::chess
