#include <gtest/gtest.h>

#include <limits>

#include "motion/coordinate_mapper.hpp"
#include "motion/motion_planner.hpp"

namespace ac::motion {
namespace {

CoordinateMapper calibratedBoardMapper()
{
    CoordinateMapper mapper("");
    mapper.calibrateBoard({0.0, 0.0}, {70.0, 0.0});
    return mapper;
}

TEST(MotionPlannerTest, ReturnsPredefinedPoses)
{
    auto mapper = calibratedBoardMapper();
    MotionPlanner planner(mapper);

    const Pose home = planner.getPredefinedPose(PredefinedPosition::HOME);
    const Pose staging =
        planner.getPredefinedPose(PredefinedPosition::SAFE_STAGING);

    EXPECT_DOUBLE_EQ(home.x, 0.0);
    EXPECT_DOUBLE_EQ(home.y, 0.0);
    EXPECT_DOUBLE_EQ(home.z, 150.0);
    EXPECT_DOUBLE_EQ(staging.z, 100.0);
}

TEST(MotionPlannerTest, PlansSafeEightPoseTransfer)
{
    auto mapper = calibratedBoardMapper();
    MotionPlanner planner(mapper, 50.0, 10.0);

    const auto trajectory =
        planner.planTransfer({20.0, 30.0}, {80.0, 90.0});

    ASSERT_EQ(trajectory.size(), 8u);

    EXPECT_EQ(trajectory[0].label, "APPROACH_SOURCE");
    EXPECT_DOUBLE_EQ(trajectory[0].z, 50.0);
    EXPECT_DOUBLE_EQ(trajectory[0].gripperPercent, 100.0);

    EXPECT_EQ(trajectory[1].label, "LOWER_TO_SOURCE");
    EXPECT_DOUBLE_EQ(trajectory[1].z, 10.0);
    EXPECT_DOUBLE_EQ(trajectory[1].gripperPercent, 100.0);

    EXPECT_EQ(trajectory[2].label, "GRASP_PIECE");
    EXPECT_DOUBLE_EQ(trajectory[2].gripperPercent, 0.0);

    EXPECT_EQ(trajectory[3].label, "LIFT_PIECE");
    EXPECT_DOUBLE_EQ(trajectory[3].z, 50.0);

    EXPECT_EQ(trajectory[4].label, "APPROACH_TARGET");
    EXPECT_DOUBLE_EQ(trajectory[4].x, 80.0);
    EXPECT_DOUBLE_EQ(trajectory[4].y, 90.0);
    EXPECT_DOUBLE_EQ(trajectory[4].z, 50.0);

    EXPECT_EQ(trajectory[6].label, "RELEASE_PIECE");
    EXPECT_DOUBLE_EQ(trajectory[6].gripperPercent, 100.0);

    EXPECT_EQ(trajectory[7].label, "RETRACT");
    EXPECT_DOUBLE_EQ(trajectory[7].z, 50.0);
}

TEST(MotionPlannerTest, PlansBoardMoveFromCoordinateMapper)
{
    auto mapper = calibratedBoardMapper();
    MotionPlanner planner(mapper);

    const auto trajectory = planner.planBoardMove("e2", "e4");

    ASSERT_EQ(trajectory.size(), 8u);
    EXPECT_NEAR(trajectory.front().x, 40.0, 1e-9);
    EXPECT_NEAR(trajectory.front().y, 10.0, 1e-9);
    EXPECT_NEAR(trajectory[4].x, 40.0, 1e-9);
    EXPECT_NEAR(trajectory[4].y, 30.0, 1e-9);
}

TEST(MotionPlannerTest, RejectsUnsafeHeightConfiguration)
{
    auto mapper = calibratedBoardMapper();

    EXPECT_THROW(
        MotionPlanner(mapper, 10.0, 10.0),
        std::invalid_argument
    );
}

TEST(MotionPlannerTest, RejectsNonFinitePhysicalPoint)
{
    auto mapper = calibratedBoardMapper();
    MotionPlanner planner(mapper);

    const double nan = std::numeric_limits<double>::quiet_NaN();

    EXPECT_THROW(
        planner.planTransfer({nan, 0.0}, {0.0, 0.0}),
        std::invalid_argument
    );
}

} // namespace
} // namespace ac::motion
