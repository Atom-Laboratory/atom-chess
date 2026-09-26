#include <gtest/gtest.h>
#include <stdexcept>
#include "../include/motion/motion_planner.hpp"

using namespace ac::motion;

class MotionPlannerTest : public ::testing::Test {
protected:
    CoordinateMapperMock mapper;
    MotionPlanner planner{mapper, 50.0, 10.0};
};

TEST_F(MotionPlannerTest, GraveyardAllocationTypeSeparation) {
    // Allocating a white pawn must not consume a white rook slot.
    Pose pawnPose = planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn);
    Pose rookPose = planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Rook);

    // Pawns and rooks occupy different graveyard rows.
    EXPECT_NE(pawnPose.y, rookPose.y);

    // Fill the maximum white-pawn capacity.
    for (int i = 0; i < 7; ++i) {
        EXPECT_NO_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn));
    }

    // A ninth white pawn exceeds the physical allocation.
    EXPECT_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn), std::out_of_range);

    // Rook allocation remains independent.
    EXPECT_NO_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Rook));
}

TEST_F(MotionPlannerTest, GraveyardColorIndependence) {
    // White and black graveyards are independent.
    Pose whitePawn = planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn);
    Pose blackPawn = planner.allocateNextGraveyardPose(PieceColor::Black, PieceType::Pawn);

    // Different base locations must produce distinct coordinates.
    EXPECT_NE(whitePawn.x, blackPawn.x);
}

TEST_F(MotionPlannerTest, InvalidPieceTypeHandling) {
    // Missing color/type is invalid.
    EXPECT_THROW(planner.allocateNextGraveyardPose(PieceColor::None, PieceType::Pawn), std::invalid_argument);
    EXPECT_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::None), std::invalid_argument);
}

TEST_F(MotionPlannerTest, ResetGraveyard) {
    // Fill the white-pawn area.
    for (int i = 0; i < 8; ++i) {
        planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn);
    }
    EXPECT_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn), std::out_of_range);

    // Reset makes the area available again.
    planner.resetGraveyards();
    EXPECT_NO_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn));
}

TEST_F(MotionPlannerTest, PredefinedPoses)
{
    const Pose home = planner.getPredefinedPose(PredefinedPosition::HOME);
    EXPECT_DOUBLE_EQ(home.x, 0.0);
    EXPECT_DOUBLE_EQ(home.y, 0.0);
    EXPECT_DOUBLE_EQ(home.z, 150.0);
}

TEST_F(MotionPlannerTest, PlanBasicMovePreservesSafeGripperSequence)
{
    const auto trajectory = planner.planMove("e2", "e4");

    ASSERT_EQ(trajectory.size(), 8u);

    EXPECT_EQ(trajectory[0].label, "APPROACH_SOURCE");
    EXPECT_DOUBLE_EQ(trajectory[0].gripper_percent, 100.0);

    EXPECT_EQ(trajectory[1].label, "LOWER_TO_SOURCE");
    EXPECT_DOUBLE_EQ(trajectory[1].z, 10.0);
    EXPECT_DOUBLE_EQ(trajectory[1].gripper_percent, 100.0);

    EXPECT_EQ(trajectory[2].label, "GRASP_PIECE");
    EXPECT_DOUBLE_EQ(trajectory[2].z, 10.0);
    EXPECT_DOUBLE_EQ(trajectory[2].gripper_percent, 0.0);

    EXPECT_EQ(trajectory[3].label, "LIFT_PIECE");
    EXPECT_DOUBLE_EQ(trajectory[3].z, 50.0);
    EXPECT_DOUBLE_EQ(trajectory[3].gripper_percent, 0.0);

    EXPECT_EQ(trajectory[6].label, "RELEASE_PIECE");
    EXPECT_DOUBLE_EQ(trajectory[6].gripper_percent, 100.0);

    EXPECT_EQ(trajectory[7].label, "RETRACT");
    EXPECT_DOUBLE_EQ(trajectory[7].z, 50.0);
}
