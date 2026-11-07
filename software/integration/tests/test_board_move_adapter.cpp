#include <array>
#include <stdexcept>

#include <gtest/gtest.h>

#include "integration/board_move_adapter.hpp"
#include "integration/engine_turn_planner.hpp"
#include "board/move_applier.hpp"
#include "board/move_validator.hpp"
#include "fen_generator/fen_generator.hpp"
#include "motion/task_planner.hpp"

namespace ac::integration {
namespace {

TEST(EngineTurnPlanner, ValidatesUciAndDerivesSpecialMoveFlags)
{
    chess::Board board;
    EXPECT_FALSE(chess::MoveValidator::validateUci(board, "e2e5"));
    EXPECT_FALSE(chess::MoveValidator::validateUci(board, "e7e5"));
    EXPECT_FALSE(chess::MoveValidator::validateUci(board, "e2e4q"));
    const auto apply = [&](std::string_view token) {
        const auto move = chess::MoveValidator::validateUci(board, token);
        ASSERT_TRUE(move.has_value());
        chess::MoveApplier::apply(board, *move);
    };
    apply("e2e4");
    apply("a7a6");
    apply("e4e5");
    apply("d7d5");
    const auto capture = chess::MoveValidator::validateUci(board, "e5d6");
    ASSERT_TRUE(capture.has_value());
    EXPECT_TRUE(capture->capture);
    EXPECT_TRUE(capture->enPassant);
    EXPECT_FALSE(chess::MoveValidator::validateUci(board, "e5d6q"));
}

#ifdef ATOM_TEST_STOCKFISH
TEST(EngineTurnPlanner, PlansTwoRealEngineTurnsWithoutCommittingBoard)
{
    motion::CoordinateMapper mapper("");
    mapper.calibrateBoard({0.0, 0.0}, {70.0, 0.0});
    motion::GraveyardAllocator graveyard(mapper);
    motion::TaskPlanner planner(mapper, graveyard);
    chess::engine::StockfishUCI engine(ATOM_TEST_STOCKFISH);
    ASSERT_TRUE(engine.init());
    chess::Board board;
    for (int ply = 0; ply < 2; ++ply) {
        const auto before = chess::FenGenerator::generate(board);
        const auto plan = planEngineTurn(board, engine, planner, 5);
        ASSERT_EQ(plan.engineStatus, chess::engine::UciStatus::Success);
        ASSERT_TRUE(plan.validatedMove.has_value());
        ASSERT_EQ(plan.tasks.size(), 1U);
        EXPECT_EQ(plan.tasks[0].boardSource, plan.validatedMove->from);
        EXPECT_EQ(plan.tasks[0].boardTarget, plan.validatedMove->to);
        EXPECT_NO_THROW((void)serializeBoardMove(plan.tasks));
        EXPECT_EQ(chess::FenGenerator::generate(board), before);
        // The test advances the logical position explicitly between queries.
        chess::MoveApplier::apply(board, *plan.validatedMove);
    }
}
#endif

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
    EXPECT_EQ(serializeBoardMove(plan),
        R"({"schema":1,"operation":"MOVE","source":"e2","target":"e3"})");
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

TEST(BoardMoveAdapter, SerializesOrderedCaptureAndRejectsPromotion)
{
    std::array<motion::PhysicalTask, 2> plan{};
    plan[0].type = motion::PhysicalTaskType::RemoveCapturedPiece;
    plan[0].boardSource = chess::Square{4, 3};
    plan[0].physicalTarget = motion::Point2D{100., 200.};
    plan[1].boardSource = chess::Square{5, 4};
    plan[1].boardTarget = chess::Square{4, 3};
    const auto resolve = [](motion::Point2D point) {
        EXPECT_DOUBLE_EQ(point.x, 100.);
        EXPECT_DOUBLE_EQ(point.y, 200.);
        return "slot_0";
    };
    EXPECT_EQ(serializePhysicalPlan(plan, resolve),
        R"({"schema":2,"operation":"PLAN","transfers":[{"source":"d4","target":"graveyard:slot_0"},{"source":"e3","target":"d4"}]})");
    EXPECT_THROW((void)serializePhysicalPlan(plan, {}), std::invalid_argument);
    plan[1].type = motion::PhysicalTaskType::PromotionRequired;
    EXPECT_THROW((void)serializePhysicalPlan(plan, resolve), std::invalid_argument);
}

}
}
