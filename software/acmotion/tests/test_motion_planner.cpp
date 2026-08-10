#include <gtest/gtest.h>
#include "motion/motion_planner.hpp"
#include <stdexcept>

using namespace ac::motion;

class MotionPlannerTest : public ::testing::Test {
protected:
    CoordinateMapperMock mapper;
    MotionPlanner planner{mapper, 50.0, 10.0};
};

TEST_F(MotionPlannerTest, PredefinedPosesReturnCorrectCoordinates) {
    Pose home = planner.getPredefinedPose(PredefinedPosition::HOME);
    EXPECT_EQ(home.x, 0.0);
    EXPECT_EQ(home.y, 0.0);
    EXPECT_EQ(home.z, 150.0);

    Pose whiteBase = planner.getPredefinedPose(PredefinedPosition::GRAVEYARD_WHITE);
    EXPECT_EQ(whiteBase.x, 200.0);
    EXPECT_EQ(whiteBase.y, -100.0);

    Pose blackBase = planner.getPredefinedPose(PredefinedPosition::GRAVEYARD_BLACK);
    EXPECT_EQ(blackBase.x, -200.0);
    EXPECT_EQ(blackBase.y, -100.0);
}

TEST_F(MotionPlannerTest, GraveyardMatrixSlotCalculation) {
    // Test slot 0 (row 0, col 0)
    Pose whiteSlot0 = planner.getGraveyardSlotPose(PieceColor::WHITE, 0);
    EXPECT_EQ(whiteSlot0.x, 200.0);
    EXPECT_EQ(whiteSlot0.y, -100.0);

    // Test slot 1 (row 0, col 1 -> +20mm in X)
    Pose whiteSlot1 = planner.getGraveyardSlotPose(PieceColor::WHITE, 1);
    EXPECT_EQ(whiteSlot1.x, 220.0);
    EXPECT_EQ(whiteSlot1.y, -100.0);

    // Test slot 8 (row 1, col 0 -> +20mm in Y)
    Pose whiteSlot8 = planner.getGraveyardSlotPose(PieceColor::WHITE, 8);
    EXPECT_EQ(whiteSlot8.x, 200.0);
    EXPECT_EQ(whiteSlot8.y, -80.0);
}

TEST_F(MotionPlannerTest, SequentialAllocationAdvancesSlots) {
    planner.resetGraveyards();

    Pose firstPiece = planner.allocateNextGraveyardPose(PieceColor::WHITE);
    EXPECT_EQ(firstPiece.label, "GRAVEYARD_WHITE_SLOT_0");

    Pose secondPiece = planner.allocateNextGraveyardPose(PieceColor::WHITE);
    EXPECT_EQ(secondPiece.label, "GRAVEYARD_WHITE_SLOT_1");

    // Check that black graveyard index remains independent
    Pose blackPiece = planner.allocateNextGraveyardPose(PieceColor::BLACK);
    EXPECT_EQ(blackPiece.label, "GRAVEYARD_BLACK_SLOT_0");
}

TEST_F(MotionPlannerTest, GraveyardCapacityThrowsOnOverflow) {
    planner.resetGraveyards();

    for (std::size_t i = 0; i < 16; ++i) {
        EXPECT_NO_THROW(planner.allocateNextGraveyardPose(PieceColor::WHITE));
    }

    // 17th piece should throw out_of_range
    EXPECT_THROW(planner.allocateNextGraveyardPose(PieceColor::WHITE), std::out_of_range);
}

TEST_F(MotionPlannerTest, PlanMoveGeneratesExpectedTrajectorySize) {
    auto trajectory = planner.planMove("e2", "e4");
    EXPECT_EQ(trajectory.size(), 8);
}