#include <array>
#include <stdexcept>

#include <gtest/gtest.h>

#include "integration/board_move_adapter.hpp"
#include "motion/task_planner.hpp"

namespace ac::integration {
namespace {

TEST(BoardMoveAdapter, AdaptsRealTaskPlannerOutputFromChessCore)
{
    motion::CoordinateMapper mapper("");
    mapper.calibrateBoard({0.0, 0.0}, {70.0, 0.0});
    motion::GraveyardAllocator graveyard(mapper);
    motion::TaskPlanner planner(mapper, graveyard);
    const chess::Board board;
    const auto plan = planner.planTasks(board, chess::Move{.from = {6, 4}, .to = {5, 4}});

    const auto request = adaptBoardMove(plan);
    EXPECT_EQ(request.source, "e2");
    EXPECT_EQ(request.target, "e3");
}

TEST(BoardMoveAdapter, RejectsWholeCapturePlanAndUnsupportedSingletons)
{
    motion::PhysicalTask removal{.type = motion::PhysicalTaskType::RemoveCapturedPiece};
    motion::PhysicalTask move{.boardSource = chess::Square{6, 4},
                              .boardTarget = chess::Square{5, 4}};
    EXPECT_THROW((void)adaptBoardMove((std::array{removal, move})), std::invalid_argument);
    EXPECT_THROW((void)adaptBoardMove((std::array{removal})), std::invalid_argument);
    EXPECT_THROW((void)adaptBoardMove({}), std::invalid_argument);
}

TEST(BoardMoveAdapter, RejectsInvalidBoardEndpoints)
{
    std::array<motion::PhysicalTask, 1> plan{};
    EXPECT_THROW((void)adaptBoardMove(plan), std::invalid_argument);
    plan[0].boardSource = chess::Square{6, 4};
    plan[0].boardTarget = plan[0].boardSource;
    EXPECT_THROW((void)adaptBoardMove(plan), std::invalid_argument);
    plan[0].boardTarget = chess::Square{8, 4};
    EXPECT_THROW((void)adaptBoardMove(plan), std::invalid_argument);
}

}
}
