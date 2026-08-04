#include <gtest/gtest.h>
#include "../include/motion/motion_planner.hpp"

using namespace ac::motion;

// Teste de Poses Pré-definidas
TEST(MotionPlannerTest, PredefinedPoses) {
    CoordinateMapperMock mapper;
    MotionPlanner planner(mapper);

    Pose home = planner.getPredefinedPose(PredefinedPosition::HOME);
    EXPECT_DOUBLE_EQ(home.x, 0.0);
    EXPECT_DOUBLE_EQ(home.y, 0.0);
    EXPECT_DOUBLE_EQ(home.z, 150.0);
}

// Teste de geração de trajetória básica (planMove)
TEST(MotionPlannerTest, PlanBasicMove) {
    CoordinateMapperMock mapper;
    MotionPlanner planner(mapper);

    auto trajectory = planner.planMove("e2", "e4");

    // Garante que a trajetória foi gerada
    EXPECT_FALSE(trajectory.empty());
}