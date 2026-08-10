#ifndef ACMOTION_MOTION_PLANNER_HPP
#define ACMOTION_MOTION_PLANNER_HPP

#include <string>
#include <vector>
#include <utility>
#include <cstddef>

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
    GRAVEYARD,         ///< Legacy generic graveyard position
    GRAVEYARD_WHITE,   ///< Base position for white pieces 2x8 graveyard matrix
    GRAVEYARD_BLACK,   ///< Base position for black pieces 2x8 graveyard matrix
    SAFE_STAGING
};

/**
 * @enum PieceColor
 * @brief Represents the color of a chess piece for graveyard matrix indexing.
 */
enum class PieceColor {
    WHITE,
    BLACK
};

/**
 * @struct Pose
 * @brief Represents a 3D Cartesian position, gripper aperture percentage, and debug label.
 */
struct Pose {
    double x{0.0};               ///< X-coordinate in mm
    double y{0.0};               ///< Y-coordinate in mm
    double z{0.0};               ///< Z-coordinate in mm
    double gripper_percent{0.0}; ///< Gripper opening percentage (0.0 = fully closed, 100.0 = fully open)
    std::string label;          ///< Descriptive tag for debugging and logging
};

/**
 * @class CoordinateMapperMock
 * @brief Mock implementation of the CoordinateMapper interface for board cell translation during testing.
 */
class CoordinateMapperMock {
public:
    virtual ~CoordinateMapperMock() = default;

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
     * @param safeHeightZ Clearance height in Z (mm) to avoid collisions.
     * @param pickHeightZ Height in Z (mm) for gripping/releasing pieces.
     */
    MotionPlanner(const CoordinateMapperMock& mapper, 
                  double safeHeightZ = 50.0, 
                  double pickHeightZ = 10.0);

    /**
     * @brief Generates a trajectory to move a piece from source cell to target cell.
     */
    std::vector<Pose> planMove(const std::string& from, const std::string& to);

    /**
     * @brief Returns a predefined pose based on the state machine Enum.
     */
    Pose getPredefinedPose(PredefinedPosition pos) const;

    /**
     * @brief Gets the pose for a specific slot in the 2x8 graveyard matrix of a given color.
     * @param color Color of the captured piece (WHITE or BLACK).
     * @param slotIndex Slot index within the 2x8 grid (0 to 15).
     * @return Pose Cartesian position corresponding to the matrix slot.
     */
    Pose getGraveyardSlotPose(PieceColor color, std::size_t slotIndex) const;

    /**
     * @brief Plans a capture trajectory, sending the captured piece to the next free graveyard slot.
     * @param color Color of the captured piece.
     * @return Pose Cartesian position of the allocated graveyard slot.
     */
    Pose allocateNextGraveyardPose(PieceColor color);

    /**
     * @brief Resets graveyard occupation indices back to slot 0.
     */
    void resetGraveyards();

private:
    const CoordinateMapperMock& mapper_;
    double safeHeightZ_;
    double pickHeightZ_;

    std::size_t white_graveyard_index_{0};
    std::size_t black_graveyard_index_{0};

    static constexpr double GRIPPER_OPEN = 100.0;
    static constexpr double GRIPPER_CLOSED = 0.0;
    static constexpr std::size_t GRAVEYARD_CAPACITY = 16; // 2x8 matrix

    const Pose HOME_POSE = {0.0, 0.0, 150.0, GRIPPER_OPEN, "HOME"};
    const Pose GRAVEYARD_POSE = {200.0, -100.0, 50.0, GRIPPER_OPEN, "GRAVEYARD"};
    const Pose GRAVEYARD_WHITE_BASE = {200.0, -100.0, 50.0, GRIPPER_OPEN, "GRAVEYARD_WHITE"};
    const Pose GRAVEYARD_BLACK_BASE = {-200.0, -100.0, 50.0, GRIPPER_OPEN, "GRAVEYARD_BLACK"};

    static constexpr double SLOT_SPACING_X = 20.0;
    static constexpr double SLOT_SPACING_Y = 20.0;
};

} // namespace ac::motion

#endif // ACMOTION_MOTION_PLANNER_HPP