#include <gtest/gtest.h>

#include <numbers>
#include <cmath>

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
    EXPECT_NEAR(target->joint3Rad, 0.0, 1e-9);
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
    EXPECT_NEAR(target->joint3Rad, -std::numbers::pi / 2.0, 1e-9);
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
    EXPECT_NEAR(target->joint3Rad, 0.0, 1e-9);
}

TEST(InverseKinematicsTest, RejectsPointOutsideRadialWorkspace)
{
    InverseKinematics ik(defaultGeometry());

    EXPECT_FALSE(
        ik.solve(Pose{250.0, 0.0, 20.0, 100.0, "TEST"}).has_value()
    );
}

TEST(InverseKinematicsTest, AcceptsInnerBoundaryAtInclusiveShoulderLimit)
{
    for (auto elbow : {ElbowConfiguration::Up, ElbowConfiguration::Down}) {
        auto geometry = defaultGeometry(elbow);
        geometry.link2Mm = 50.0;
        geometry.limits.joint1MinRad = 0.0;
        geometry.limits.joint1MaxRad = 0.0;
        const InverseKinematics ik(geometry);

        const auto target = ik.solve(Pose{50.0, 0.0, 20.0, 50.0, "INNER"});

        ASSERT_TRUE(target.has_value());
        const double expectedElbow = elbow == ElbowConfiguration::Up
            ? std::numbers::pi : -std::numbers::pi;
        EXPECT_DOUBLE_EQ(target->joint1Rad, 0.0);
        EXPECT_DOUBLE_EQ(target->joint2Rad, expectedElbow);
        EXPECT_DOUBLE_EQ(target->joint3Rad, -expectedElbow);
    }
}

TEST(InverseKinematicsTest, PreservesFoldedOriginConvention)
{
    for (auto elbow : {ElbowConfiguration::Up, ElbowConfiguration::Down}) {
        const InverseKinematics ik(defaultGeometry(elbow));
        const auto target = ik.solve(Pose{0.0, 0.0, 20.0, 50.0, "ORIGIN"});

        ASSERT_TRUE(target.has_value());
        const double expectedElbow = elbow == ElbowConfiguration::Up
            ? std::numbers::pi : -std::numbers::pi;
        EXPECT_NEAR(target->joint1Rad, -expectedElbow / 2.0, 1e-9);
        EXPECT_NEAR(target->joint2Rad, expectedElbow, 1e-9);
        EXPECT_NEAR(target->joint3Rad, -expectedElbow / 2.0, 1e-9);
    }
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
        (void)InverseKinematics{geometry},
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


TEST(InverseKinematicsTest, MaintainsRequestedPlanarToolYawWithJoint3)
{
    InverseKinematics ik(defaultGeometry());

    Pose pose{100.0, 100.0, 20.0, 100.0, "TEST"};
    pose.toolYawRad = std::numbers::pi / 4.0;

    const auto target = ik.solve(pose);

    ASSERT_TRUE(target.has_value());
    EXPECT_NEAR(
        target->joint1Rad + target->joint2Rad + target->joint3Rad,
        pose.toolYawRad,
        1e-9
    );
}

TEST(InverseKinematicsTest, AppliesJoint3ZeroOffset)
{
    auto geometry = defaultGeometry();
    geometry.joint3ZeroOffsetRad = 0.25;
    InverseKinematics ik(geometry);

    Pose pose{200.0, 0.0, 20.0, 100.0, "TEST"};
    pose.toolYawRad = 0.5;

    const auto target = ik.solve(pose);

    ASSERT_TRUE(target.has_value());
    EXPECT_NEAR(target->joint3Rad, 0.25, 1e-9);
}

TEST(InverseKinematicsTest, RejectsJoint3OutsideMechanicalLimits)
{
    auto geometry = defaultGeometry();
    geometry.limits.joint3MinRad = -0.25;
    geometry.limits.joint3MaxRad = 0.25;
    InverseKinematics ik(geometry);

    Pose pose{100.0, 100.0, 20.0, 100.0, "TEST"};
    pose.toolYawRad = std::numbers::pi;

    EXPECT_FALSE(ik.solve(pose).has_value());
}

TEST(InverseKinematicsTest, ForwardKinematicsRoundTripsBothConfiguredBranches)
{
    for (const auto elbow : {ElbowConfiguration::Up, ElbowConfiguration::Down}) {
        auto geometry = defaultGeometry(elbow);
        geometry.link2Mm = 70.0;
        geometry.joint3ZeroOffsetRad = 0.2;
        InverseKinematics ik(geometry);
        for (double shoulder : {-0.8, -0.2, 0.0, 0.4, 0.8}) {
            for (double bend : {0.1, 0.5, 1.0, 1.8}) {
                const double j2 = elbow == ElbowConfiguration::Up ? bend : -bend;
                for (double z : {0.0, 50.0, 200.0}) {
                    Pose pose{100.0 * std::cos(shoulder) + 70.0 * std::cos(shoulder + j2),
                              100.0 * std::sin(shoulder) + 70.0 * std::sin(shoulder + j2),
                              z, 37.0, "FK_VALIDATION"};
                    pose.toolYawRad = shoulder + j2 + 0.3 + 0.2;
                    const auto target = ik.solve(pose);
                    ASSERT_TRUE(target.has_value());
                    EXPECT_NEAR(target->joint1Rad, shoulder, 1e-10);
                    EXPECT_NEAR(target->joint2Rad, j2, 1e-10);
                    EXPECT_NEAR(target->joint3Rad, 0.3, 1e-10);
                    EXPECT_NEAR(100.0 * std::cos(target->joint1Rad)
                        + 70.0 * std::cos(target->joint1Rad + target->joint2Rad), pose.x, 1e-9);
                    EXPECT_NEAR(100.0 * std::sin(target->joint1Rad)
                        + 70.0 * std::sin(target->joint1Rad + target->joint2Rad), pose.y, 1e-9);
                    EXPECT_DOUBLE_EQ(target->zMm, z);
                    EXPECT_DOUBLE_EQ(target->gripperPercent, 37.0);
                }
            }
        }
    }
}

TEST(InverseKinematicsTest, AcceptsInclusiveInnerBoundaryForBothBranches)
{
    for (const auto elbow : {ElbowConfiguration::Up, ElbowConfiguration::Down}) {
        auto geometry = defaultGeometry(elbow);
        geometry.link2Mm = 50.0;
        geometry.limits.joint1MinRad = 0.0;
        geometry.limits.joint1MaxRad = 0.0;
        const auto target = InverseKinematics(geometry).solve(Pose{50, 0, 20, 100, "BOUNDARY"});
        ASSERT_TRUE(target.has_value());
        EXPECT_DOUBLE_EQ(target->joint1Rad, 0.0);
        EXPECT_NEAR(std::abs(target->joint2Rad), std::numbers::pi, 1e-12);
        EXPECT_FALSE(InverseKinematics(geometry).solve(Pose{49, 0, 20, 100, "INNER"}));
    }
}

TEST(InverseKinematicsTest, PreservesEqualLinkFoldedOriginConvention)
{
    for (const auto elbow : {ElbowConfiguration::Up, ElbowConfiguration::Down}) {
        const auto target = InverseKinematics(defaultGeometry(elbow)).solve(Pose{0, 0, 20, 100, "ORIGIN"});
        ASSERT_TRUE(target.has_value());
        const double sign = elbow == ElbowConfiguration::Up ? 1.0 : -1.0;
        EXPECT_NEAR(target->joint1Rad, -sign * std::numbers::pi / 2, 1e-12);
        EXPECT_NEAR(target->joint2Rad, sign * std::numbers::pi, 1e-12);
    }
}

TEST(InverseKinematicsTest, DoesNotSilentlyFallbackToAlternativeBranch)
{
    auto geometry = defaultGeometry();
    geometry.limits.joint2MaxRad = 0.5;
    const Pose pose{100, 100, 20, 100, "BRANCH_POLICY"};
    EXPECT_FALSE(InverseKinematics(geometry).solve(pose));
    geometry.preferredElbow = ElbowConfiguration::Down;
    EXPECT_TRUE(InverseKinematics(geometry).solve(pose));
}

TEST(InverseKinematicsTest, DoesNotSilentlyWrapBoundedWristTravel)
{
    InverseKinematics ik(defaultGeometry());
    Pose pose{200, 0, 20, 100, "WRIST_POLICY"};
    pose.toolYawRad = 2 * std::numbers::pi;
    EXPECT_FALSE(ik.solve(pose));
    pose.toolYawRad = 0.0;
    EXPECT_TRUE(ik.solve(pose));
}

} // namespace
} // namespace ac::motion
