#include <gtest/gtest.h>

#include "board/board.hpp"
#include "board/move.hpp"
#include "motion/coordinate_mapper.hpp"
#include "motion/graveyard_allocator.hpp"
#include "motion/task_planner.hpp"

namespace ac::motion {
namespace {

CoordinateMapper configuredMapper()
{
    CoordinateMapper mapper("");
    mapper.calibrateBoard({0.0, 0.0}, {70.0, 0.0});

    GridGeometry white;
    white.origin = {100.0, -40.0};
    white.columnStep = {10.0, 0.0};
    white.rowStep = {0.0, 10.0};

    GridGeometry black;
    black.origin = {-100.0, -40.0};
    black.columnStep = {-10.0, 0.0};
    black.rowStep = {0.0, 10.0};

    mapper.setGraveyardGeometry(GraveyardSide::WHITE, white);
    mapper.setGraveyardGeometry(GraveyardSide::BLACK, black);
    return mapper;
}

TEST(TaskPlannerTest, PlansNormalMoveAsSingleBoardTransfer)
{
    auto mapper = configuredMapper();
    GraveyardAllocator graveyard(mapper);
    TaskPlanner planner(mapper, graveyard);
    ac::chess::Board board;

    const ac::chess::Move move{
        .from = {6, 4},
        .to = {4, 4}
    };

    const auto tasks = planner.planTasks(board, move);

    ASSERT_EQ(tasks.size(), 1u);
    EXPECT_EQ(tasks[0].type, PhysicalTaskType::MoveBoardPiece);
    EXPECT_EQ(tasks[0].boardSource, (ac::chess::Square{6, 4}));
    EXPECT_EQ(tasks[0].boardTarget, (ac::chess::Square{4, 4}));
    ASSERT_TRUE(tasks[0].physicalSource.has_value());
    ASSERT_TRUE(tasks[0].physicalTarget.has_value());
}

TEST(TaskPlannerTest, RemovesCapturedPieceBeforeMovingAttacker)
{
    auto mapper = configuredMapper();
    GraveyardAllocator graveyard(mapper);
    TaskPlanner planner(mapper, graveyard);

    ac::chess::Board board;
    board.clear();
    board.setPiece({4, 2}, {
        ac::chess::PieceType::Bishop,
        ac::chess::PieceColor::White
    });
    board.setPiece({3, 3}, {
        ac::chess::PieceType::Pawn,
        ac::chess::PieceColor::Black
    });

    const ac::chess::Move move{
        .from = {4, 2},
        .to = {3, 3},
        .capture = true
    };

    const auto tasks = planner.planTasks(board, move);

    ASSERT_EQ(tasks.size(), 2u);
    EXPECT_EQ(tasks[0].type, PhysicalTaskType::RemoveCapturedPiece);
    EXPECT_EQ(tasks[0].piece.type, ac::chess::PieceType::Pawn);
    EXPECT_EQ(tasks[1].type, PhysicalTaskType::MoveBoardPiece);
}

TEST(TaskPlannerTest, RemovesCorrectPawnForEnPassant)
{
    auto mapper = configuredMapper();
    GraveyardAllocator graveyard(mapper);
    TaskPlanner planner(mapper, graveyard);

    ac::chess::Board board;
    board.clear();
    board.setPiece({3, 4}, {
        ac::chess::PieceType::Pawn,
        ac::chess::PieceColor::White
    });
    board.setPiece({3, 3}, {
        ac::chess::PieceType::Pawn,
        ac::chess::PieceColor::Black
    });

    const ac::chess::Move move{
        .from = {3, 4},
        .to = {2, 3},
        .capture = true,
        .enPassant = true
    };

    const auto tasks = planner.planTasks(board, move);

    ASSERT_EQ(tasks.size(), 2u);
    EXPECT_EQ(tasks[0].type, PhysicalTaskType::RemoveCapturedPiece);
    EXPECT_EQ(tasks[0].boardSource, (ac::chess::Square{3, 3}));
    EXPECT_EQ(tasks[1].boardTarget, (ac::chess::Square{2, 3}));
}

TEST(TaskPlannerTest, CastlingMovesKingThenRook)
{
    auto mapper = configuredMapper();
    GraveyardAllocator graveyard(mapper);
    TaskPlanner planner(mapper, graveyard);

    ac::chess::Board board;
    board.clear();
    board.setPiece({7, 4}, {
        ac::chess::PieceType::King,
        ac::chess::PieceColor::White
    });
    board.setPiece({7, 7}, {
        ac::chess::PieceType::Rook,
        ac::chess::PieceColor::White
    });

    const ac::chess::Move move{
        .from = {7, 4},
        .to = {7, 6},
        .castle = true
    };

    const auto tasks = planner.planTasks(board, move);

    ASSERT_EQ(tasks.size(), 2u);
    EXPECT_EQ(tasks[0].piece.type, ac::chess::PieceType::King);
    EXPECT_EQ(tasks[0].boardTarget, (ac::chess::Square{7, 6}));
    EXPECT_EQ(tasks[1].piece.type, ac::chess::PieceType::Rook);
    EXPECT_EQ(tasks[1].boardSource, (ac::chess::Square{7, 7}));
    EXPECT_EQ(tasks[1].boardTarget, (ac::chess::Square{7, 5}));
}

TEST(TaskPlannerTest, PromotionIsExplicitInsteadOfAssumedPhysicalReplacement)
{
    auto mapper = configuredMapper();
    GraveyardAllocator graveyard(mapper);
    TaskPlanner planner(mapper, graveyard);

    ac::chess::Board board;
    board.clear();
    board.setPiece({1, 0}, {
        ac::chess::PieceType::Pawn,
        ac::chess::PieceColor::White
    });

    const ac::chess::Move move{
        .from = {1, 0},
        .to = {0, 0},
        .promotion = ac::chess::PieceType::Queen
    };

    const auto tasks = planner.planTasks(board, move);

    ASSERT_EQ(tasks.size(), 2u);
    EXPECT_EQ(tasks[0].type, PhysicalTaskType::MoveBoardPiece);
    EXPECT_EQ(tasks[1].type, PhysicalTaskType::PromotionRequired);
    EXPECT_EQ(tasks[1].piece.type, ac::chess::PieceType::Queen);
}

TEST(TaskPlannerTest, RejectsMoveFromEmptySource)
{
    auto mapper = configuredMapper();
    GraveyardAllocator graveyard(mapper);
    TaskPlanner planner(mapper, graveyard);

    ac::chess::Board board;
    board.clear();

    EXPECT_THROW(
        (void)planner.planTasks(
            board,
            ac::chess::Move{.from = {4, 4}, .to = {3, 4}}
        ),
        std::invalid_argument
    );
}

} // namespace
} // namespace ac::motion
