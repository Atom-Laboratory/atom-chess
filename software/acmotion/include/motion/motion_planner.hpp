#ifndef ACMOTION_MOTION_PLANNER_HPP
#define ACMOTION_MOTION_PLANNER_HPP

#include <string>
#include <vector>
#include <utility>

/**
 * @file motion_planner.hpp
 * @brief Trajectory planning and motion execution interface for the SCARA robot.
 */

namespace ac::motion {

/**
 * @enum PredefinedPosition
 * @brief Predefined target positions for state machine transitions.
 */
enum class PredefinedPosition {
    HOME,
    GRAVEYARD,
    SAFE_STAGING
};

/**
 * @struct Pose
 * @brief Represents a 3D Cartesian position, gripper aperture percentage, and debug label.
 */
struct Pose {
    double x{0.0};              ///< X-coordinate in mm (Cartesian space)
    double y{0.0};              ///< Y-coordinate in mm (Cartesian space)
    double z{0.0};              ///< Z-coordinate in mm (Cartesian space)
    double gripper_percent{0.0};///< Gripper opening percentage (0.0 = fully closed, 100.0 = fully open)
    std::string label;          ///< Descriptive tag for debugging and logging (e.g., "HOME", "PICK", "PLACE")
};

/**
 * @class CoordinateMapperMock
 * @brief Mock implementation of the CoordinateMapper interface for board cell translation during testing.
 */
class CoordinateMapperMock {
public:
    virtual ~CoordinateMapperMock() = default;

    /**
     * @brief Translates an algebraic chess square (e.g., "e4") to Cartesian 2D coordinates (X, Y).
     * @param square Algebraic notation string for the board cell.
     * @return std::pair<double, double> Cartesian coordinates {X, Y} in mm at table surface height (Z = 0).
     */
    virtual std::pair<double, double> getCoordinates(const std::string& square) const {
        (void)square;
        return {100.0, 100.0}; // Simulated fixed coordinates
    }
};

/**
 * @class MotionPlanner
 * @brief Generates high-level sequential trajectories (poses) for chess piece manipulation.
 */
class MotionPlanner {
public:
    /**
     * @brief Constructs a MotionPlanner instance.
     * @param mapper Reference to the coordinate mapper interface.
     * @param safeHeightZ Clearance height in Z (mm) to avoid colliding with other pieces during horizontal moves.
     * @param pickHeightZ Height in Z (mm) where the gripper grips or releases a chess piece.
     */
    MotionPlanner(const CoordinateMapperMock& mapper, 
                  double safeHeightZ = 50.0, 
                  double pickHeightZ = 10.0);

    /**
     * @brief Generates a trajectory to move a piece from a source cell to a target cell.
     * @param from Square notation of source position (e.g., "e2").
     * @param to Square notation of target position (e.g., "e4").
     * @return std::vector<Pose> Ordered sequence of poses representing the movement trajectory.
     */
    std::vector<Pose> planMove(const std::string& from, const std::string& to);

    /**
     * @brief Returns a predefined pose based on the state machine Enum.
     * @param pos Desired predefined position.
     * @return Pose Cartesian pose associated with the predefined position.
     */
    Pose getPredefinedPose(PredefinedPosition pos) const;

private:
    const CoordinateMapperMock& mapper_;
    double safeHeightZ_;
    double pickHeightZ_;

    static constexpr double GRIPPER_OPEN = 100.0;
    static constexpr double GRIPPER_CLOSED = 0.0;

    const Pose HOME_POSE = {0.0, 0.0, 150.0, GRIPPER_OPEN, "HOME"};
    const Pose GRAVEYARD_POSE = {200.0, -100.0, 50.0, GRIPPER_OPEN, "GRAVEYARD"};
};

} // namespace ac::motion

#endif // ACMOTION_MOTION_PLANNER_HPP