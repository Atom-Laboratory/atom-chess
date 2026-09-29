#include "motion/inverse_kinematics.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace ac::motion {
namespace {

/**
 * @brief Returns true when every scalar in a mechanical range is finite.
 */
/**
 * @brief Returns true when all configured mechanical limit scalars are finite.
 * @param limits Joint/Z limits to inspect.
 * @return true when every bound is finite.
 */
bool finiteLimits(const JointLimits& limits)
{
    return std::isfinite(limits.joint1MinRad)
        && std::isfinite(limits.joint1MaxRad)
        && std::isfinite(limits.joint2MinRad)
        && std::isfinite(limits.joint2MaxRad)
        && std::isfinite(limits.zMinMm)
        && std::isfinite(limits.zMaxMm);
}

} // namespace

/**
 * @brief Validates and stores the geometric model used by the solver.
 */
InverseKinematics::InverseKinematics(ScaraGeometry geometry)
    : geometry_(geometry)
{
    const JointLimits& limits = geometry_.limits;

    if (!std::isfinite(geometry_.link1Mm)
        || !std::isfinite(geometry_.link2Mm)
        || geometry_.link1Mm <= 0.0
        || geometry_.link2Mm <= 0.0
        || !finiteLimits(limits)
        || limits.joint1MinRad > limits.joint1MaxRad
        || limits.joint2MinRad > limits.joint2MaxRad
        || limits.zMinMm > limits.zMaxMm) {
        throw std::invalid_argument("Invalid SCARA geometry or mechanical limits");
    }
}

/**
 * @brief Solves the configured planar 2R SCARA branch for one Cartesian pose.
 *
 * Radially unreachable positions and mechanically disallowed solutions return
 * std::nullopt instead of throwing.
 */
std::optional<JointTarget> InverseKinematics::solve(const Pose& pose) const
{
    if (!std::isfinite(pose.x)
        || !std::isfinite(pose.y)
        || !std::isfinite(pose.z)
        || !std::isfinite(pose.gripperPercent)
        || pose.gripperPercent < 0.0
        || pose.gripperPercent > 100.0) {
        throw std::invalid_argument("IK pose values must be finite and valid");
    }

    const double l1 = geometry_.link1Mm;
    const double l2 = geometry_.link2Mm;
    const double radiusSquared = pose.x * pose.x + pose.y * pose.y;

    const double rawCosTheta2 =
        (radiusSquared - l1 * l1 - l2 * l2) / (2.0 * l1 * l2);

    constexpr double tolerance = 1e-12;
    if (rawCosTheta2 < -1.0 - tolerance
        || rawCosTheta2 > 1.0 + tolerance) {
        return std::nullopt;
    }

    const double cosTheta2 = std::clamp(rawCosTheta2, -1.0, 1.0);
    const double baseTheta2 = std::acos(cosTheta2);
    const double theta2 =
        geometry_.preferredElbow == ElbowConfiguration::Up
            ? baseTheta2
            : -baseTheta2;

    const double theta1 =
        std::atan2(pose.y, pose.x)
        - std::atan2(
            l2 * std::sin(theta2),
            l1 + l2 * std::cos(theta2)
        );

    JointTarget target{
        theta1,
        theta2,
        pose.z,
        pose.gripperPercent
    };

    if (!withinLimits(target)) {
        return std::nullopt;
    }

    return target;
}

/**
 * @brief Checks inclusive J1/J2/Z mechanical limits for a candidate solution.
 */
bool InverseKinematics::withinLimits(const JointTarget& target) const noexcept
{
    const JointLimits& limits = geometry_.limits;

    return target.joint1Rad >= limits.joint1MinRad
        && target.joint1Rad <= limits.joint1MaxRad
        && target.joint2Rad >= limits.joint2MinRad
        && target.joint2Rad <= limits.joint2MaxRad
        && target.zMm >= limits.zMinMm
        && target.zMm <= limits.zMaxMm;
}

/**
 * @brief Exposes the validated immutable solver geometry.
 */
const ScaraGeometry& InverseKinematics::geometry() const noexcept
{
    return geometry_;
}

} // namespace ac::motion
