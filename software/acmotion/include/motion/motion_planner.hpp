#ifndef ACMOTION_MOTION_PLANNER_HPP
#define ACMOTION_MOTION_PLANNER_HPP

#include <string>
#include <vector>

#include "motion/coordinate_mapper.hpp"
#include "motion/physical_task.hpp"

namespace ac::motion {

/**
 * @enum PredefinedPosition
 * @brief Stable non-board poses used by high-level motion flows.
 */
enum class PredefinedPosition {
    HOME,        ///< Neutral parking pose away from the board.
    SAFE_STAGING ///< Generic high-clearance staging pose.
};

/**
 * @struct Pose
 * @brief One Cartesian manipulation waypoint in the SCARA base frame.
 */
struct Pose {
    double x{0.0};               ///< X coordinate in millimetres.
    double y{0.0};               ///< Y coordinate in millimetres.
    double z{0.0};               ///< Z coordinate in millimetres.
    double gripperPercent{0.0};  ///< 0 = closed, 100 = fully open.
    std::string label;           ///< Diagnostic label for logs/tracing.
};

/**
 * @class MotionPlanner
 * @brief Expands one physical transfer into an ordered pick-and-place trajectory.
 *
 * MotionPlanner runs on the Linux SBC. It consumes calibrated Cartesian
 * coordinates and generates high-level poses. It does not interpolate step
 * pulses, access GPIO, or drive motors directly; those responsibilities belong
 * to the ESP32-S3 motion controller.
 */
class MotionPlanner {
public:
    /**
     * @brief Constructs a planner using calibrated board geometry.
     * @param mapper Coordinate mapper used by planBoardMove().
     * @param safeHeightZ Collision-clearance height in millimetres.
     * @param pickHeightZ Grasp/release height in millimetres.
     *
     * @throws std::invalid_argument when safeHeightZ is not above pickHeightZ,
     *         or when either height is non-finite.
     * @note mapper must outlive this planner.
     */
    MotionPlanner(
        const CoordinateMapper& mapper,
        double safeHeightZ = 50.0,
        double pickHeightZ = 10.0
    );

    /**
     * @brief Plans a pick-and-place transfer between two physical XY points.
     * @param source Physical source coordinate in the SCARA base frame.
     * @param target Physical destination coordinate in the SCARA base frame.
     * @return Eight ordered poses: approach, lower, grasp, lift, travel, lower,
     *         release, retract.
     *
     * @throws std::invalid_argument when either point contains non-finite values.
     */
    [[nodiscard]] std::vector<Pose> planTransfer(
        Point2D source,
        Point2D target
    ) const;

    /**
     * @brief Plans a transfer between two algebraic board squares.
     * @param from Source square such as "e2".
     * @param to Target square such as "e4".
     * @return Same eight-pose sequence produced by planTransfer().
     *
     * @throws std::runtime_error when board geometry is not calibrated.
     * @throws std::invalid_argument when notation is invalid.
     */
    [[nodiscard]] std::vector<Pose> planBoardMove(
        const std::string& from,
        const std::string& to
    ) const;

    /**
     * @brief Expands one high-level PhysicalTask into a pick-and-place trajectory.
     * @param task Task produced by TaskPlanner.
     * @return Eight-pose transfer trajectory for MoveBoardPiece or RemoveCapturedPiece.
     *
     * @throws std::invalid_argument when a transfer task lacks physical endpoints,
     *         or when task.type is PromotionRequired.
     *
     * @note PromotionRequired is intentionally not converted into motion until
     *       the project defines concrete promotion replacement hardware.
     */
    [[nodiscard]] std::vector<Pose> planTask(
        const PhysicalTask& task
    ) const;

    /**
     * @brief Returns one stable predefined pose.
     * @param position Desired predefined target.
     * @return Cartesian pose associated with the requested position.
     */
    [[nodiscard]] Pose getPredefinedPose(PredefinedPosition position) const;

private:
    /**
     * @brief Validates that a 2D physical point is finite.
     * @param point Coordinate to validate.
     * @throws std::invalid_argument when X or Y is NaN/inf.
     */
    static void validatePoint(Point2D point);

    const CoordinateMapper& mapper_; ///< Calibrated board geometry.
    double safeHeightZ_;             ///< Collision-clearance height in mm.
    double pickHeightZ_;             ///< Grasp/release height in mm.

    static constexpr double GRIPPER_OPEN = 100.0; ///< Fully open gripper command percentage.
    static constexpr double GRIPPER_CLOSED = 0.0; ///< Fully closed gripper command percentage.

    /** @brief Default neutral parking pose used outside active manipulation. */
    const Pose HOME_POSE{
        0.0, 0.0, 150.0, GRIPPER_OPEN, "HOME"
    };

    /** @brief Default high-clearance staging pose used during safe repositioning. */
    const Pose SAFE_STAGING_POSE{
        0.0, 0.0, 100.0, GRIPPER_OPEN, "SAFE_STAGING"
    };
};

} // namespace ac::motion

#endif
