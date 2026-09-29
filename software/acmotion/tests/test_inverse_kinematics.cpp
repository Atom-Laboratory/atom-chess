#include <gtest/gtest.h>

#include <numbers>

#include "motion/inverse_kinematics.hpp"

namespace ac::motion {
namespace {

ScaraGeometry defaultGeometry(
    ElbowConfiguration elbow = ElbowConfiguration::Up)
{
    ScaraGeometry geometry;
    geometry.link1Mm = 100.0;
    geometry.link2Mm = 100.0;
    geometry.limits = {
        -std::numbers::pi,
        std::numbers::pi,
        -std::numbers::pi,
        std::numbers::pi,
        0.0,
        200.0
    };
    geometry.preferredElbow = elbow;
    return geometry;
}

TEST(InverseKinematicsTest, SolvesFullyExtendedXAxis)
{
    InverseKinematics ik(defaultGeometry());

    const auto target = ik.solve(
        Pose{200.0, 0.0, 25.0, 50.0, "TEST"}
    );

    ASSERT_TRUE(target.has_value());
    EXPECT_NEAR(target->joint1Rad, 0.0, 1e-9);
    EXPECT_NEAR(target->joint2Rad, 0.0, 1e-9);
    EXPECT_DOUBLE_EQ(target->zMm, 25.0);
    EXPECT_DOUBLE_EQ(target->gripperPercent, 50.0);
}

TEST(InverseKinematicsTest, SolvesKnownElbowUpConfiguration)
{
    InverseKinematics ik(defaultGeometry(ElbowConfiguration::Up));

    const auto target = ik.solve(
        Pose{100.0, 100.0, 20.0, 100.0, "TEST"}
    );

    ASSERT_TRUE(target.has_value());
    EXPECT_NEAR(target->joint1Rad, 0.0, 1e-9);
    EXPECT_NEAR(target->joint2Rad, std::numbers::pi / 2.0, 1e-9);
}

TEST(InverseKinematicsTest, SolvesDeterministicElbowDownConfiguration)
{
    InverseKinematics ik(defaultGeometry(ElbowConfiguration::Down));

    const auto target = ik.solve(
        Pose{100.0, 100.0, 20.0, 100.0, "TEST"}
    );

    ASSERT_TRUE(target.has_value());
    EXPECT_NEAR(target->joint1Rad, std::numbers::pi / 2.0, 1e-9);
    EXPECT_NEAR(target->joint2Rad, -std::numbers::pi / 2.0, 1e-9);
}

TEST(InverseKinematicsTest, RejectsPointOutsideRadialWorkspace)
{
    InverseKinematics ik(defaultGeometry());

    EXPECT_FALSE(
        ik.solve(Pose{250.0, 0.0, 20.0, 100.0, "TEST"}).has_value()
    );
}

TEST(InverseKinematicsTest, RejectsZOutsideMechanicalLimits)
{
    InverseKinematics ik(defaultGeometry());

    EXPECT_FALSE(
        ik.solve(Pose{100.0, 100.0, 250.0, 100.0, "TEST"}).has_value()
    );
}

TEST(InverseKinematicsTest, RejectsSolutionOutsideJointLimits)
{
    auto geometry = defaultGeometry();
    geometry.limits.joint2MaxRad = 0.5;

    InverseKinematics ik(geometry);

    EXPECT_FALSE(
        ik.solve(Pose{100.0, 100.0, 20.0, 100.0, "TEST"}).has_value()
    );
}

TEST(InverseKinematicsTest, RejectsInvalidGeometry)
{
    auto geometry = defaultGeometry();
    geometry.link1Mm = 0.0;

    EXPECT_THROW(
        InverseKinematics(geometry),
        std::invalid_argument
    );
}

TEST(InverseKinematicsTest, RejectsInvalidGripperValue)
{
    InverseKinematics ik(defaultGeometry());

    EXPECT_THROW(
        (void)ik.solve(Pose{100.0, 100.0, 20.0, 120.0, "TEST"}),
        std::invalid_argument
    );
}

} // namespace
} // namespace ac::motion
