#ifndef ACMOTION_INVERSE_KINEMATICS_HPP
#define ACMOTION_INVERSE_KINEMATICS_HPP

#include <optional>

#include "motion/joint_trajectory.hpp"
#include "motion/motion_planner.hpp"

namespace ac::motion {

/**
 * @enum ElbowConfiguration
 * @brief Selects one of the two planar 2R SCARA inverse-kinematics branches.
 */
enum class ElbowConfiguration {
    Up,   ///< Positive second-joint branch.
    Down  ///< Negative second-joint branch.
};

/**
 * @struct JointLimits
 * @brief Inclusive joint-space limits used to reject mechanically invalid IK solutions.
 */
struct JointLimits {
    double joint1MinRad{-3.14159265358979323846}; ///< Minimum joint 1 angle.
    double joint1MaxRad{3.14159265358979323846};  ///< Maximum joint 1 angle.
    double joint2MinRad{-3.14159265358979323846}; ///< Minimum joint 2 angle.
    double joint2MaxRad{3.14159265358979323846};  ///< Maximum joint 2 angle.
    double zMinMm{0.0};                           ///< Minimum linear Z position.
    double zMaxMm{200.0};                         ///< Maximum linear Z position.
};

/**
 * @struct ScaraGeometry
 * @brief Geometric and mechanical configuration required by the planar SCARA solver.
 *
 * All lengths use millimetres and all angular limits use radians.
 * Values must come from measured/CAD robot geometry; this module intentionally
 * provides no project-specific hard-coded arm dimensions.
 */
struct ScaraGeometry {
    double link1Mm{0.0}; ///< Shoulder-to-elbow link length.
    double link2Mm{0.0}; ///< Elbow-to-tool-center link length.
    JointLimits limits{};///< Mechanical workspace limits.
    ElbowConfiguration preferredElbow{ElbowConfiguration::Up}; ///< Deterministic solution branch.
};

/**
 * @class InverseKinematics
 * @brief Converts Cartesian SCARA poses into joint-space targets on the Linux SBC.
 *
 * The solver implements the standard planar two-revolute-joint SCARA model:
 *
 * @f[
 * c_2 = \frac{x^2+y^2-L_1^2-L_2^2}{2L_1L_2}
 * @f]
 *
 * @f[
 * \theta_2 = \pm\arccos(c_2)
 * @f]
 *
 * @f[
 * \theta_1 = \operatorname{atan2}(y,x)
 * - \operatorname{atan2}(L_2\sin\theta_2,
 * L_1+L_2\cos\theta_2)
 * @f]
 *
 * Z and gripper values are passed through after range validation.
 *
 * The ESP32-S3 never solves IK; it receives the resulting JointTarget.
 *
 * @warning This class currently solves only planar J1/J2 position plus Z.
 *          Dejan's How To Mechatronics SCARA includes J3 for distal/tool
 *          orientation. Issue #160 must be resolved before autonomous physical
 *          execution on that arm.
 */
class InverseKinematics {
public:
    /**
     * @brief Creates a solver from measured/CAD robot geometry.
     * @param geometry Link lengths, limits and deterministic elbow preference.
     * @throws std::invalid_argument when geometry or limits are non-finite,
     *         non-positive, or internally inconsistent.
     */
    explicit InverseKinematics(ScaraGeometry geometry);

    /**
     * @brief Solves one Cartesian pose into joint space.
     * @param pose Cartesian pose in the SCARA base frame.
     * @return JointTarget when reachable and inside mechanical limits;
     *         std::nullopt when the point is outside the workspace/limits.
     * @throws std::invalid_argument when pose/gripper values are non-finite or
     *         gripper percentage lies outside [0, 100].
     */
    [[nodiscard]] std::optional<JointTarget> solve(const Pose& pose) const;

    /**
     * @brief Returns immutable geometry used by this solver.
     * @return Validated geometry, limits and deterministic elbow preference.
     */
    [[nodiscard]] const ScaraGeometry& geometry() const noexcept;

private:
    /**
     * @brief Tests whether a solved joint target satisfies all configured limits.
     * @param target Candidate joint-space solution.
     * @return true when J1/J2 and Z lie inside inclusive configured limits.
     */
    [[nodiscard]] bool withinLimits(const JointTarget& target) const noexcept;

    ScaraGeometry geometry_; ///< Validated robot geometry and limits.
};

} // namespace ac::motion

#endif
