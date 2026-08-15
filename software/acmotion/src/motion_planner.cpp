/**
 * @file motion_planner.cpp
 * @brief Implementation of the MotionPlanner trajectory generation methods.
 */

#include "motion/motion_planner.hpp"

namespace ac::motion {

MotionPlanner::MotionPlanner(const CoordinateMapperMock& mapper, 
                             double safeHeightZ, 
                             double pickHeightZ)
    : mapper_(mapper), safeHeightZ_(safeHeightZ), pickHeightZ_(pickHeightZ) {}

Pose MotionPlanner::getPredefinedPose(PredefinedPosition pos) const {
    switch (pos) {
        case PredefinedPosition::HOME:
            return HOME_POSE;
        case PredefinedPosition::GRAVEYARD:
            return GRAVEYARD_POSE;
        default:
            return HOME_POSE;
    }
}

std::vector<Pose> MotionPlanner::planMove(const std::string& from, const std::string& to) {
    std::vector<Pose> trajectory;

    auto [fromX, fromY] = mapper_.getCoordinates(from);
    auto [toX, toY]     = mapper_.getCoordinates(to);

    // 1. Move to safe height above source
    trajectory.push_back({fromX, fromY, safeHeightZ_, GRIPPER_OPEN, "APPROACH_SOURCE"});

    // 2. Lower to grasp piece
    trajectory.push_back({fromX, fromY, pickHeightZ_, GRIPPER_OPEN, "LOWER_TO_SOURCE"});

    // 3. Close gripper
    trajectory.push_back({fromX, fromY, pickHeightZ_, GRIPPER_CLOSED, "GRASP_PIECE"});

    // 4. Lift piece to safe height
    trajectory.push_back({fromX, fromY, safeHeightZ_, GRIPPER_CLOSED, "LIFT_PIECE"});

    // 5. Move horizontally to safe height above target
    trajectory.push_back({toX, toY, safeHeightZ_, GRIPPER_CLOSED, "APPROACH_TARGET"});

    // 6. Lower to target height
    trajectory.push_back({toX, toY, pickHeightZ_, GRIPPER_CLOSED, "LOWER_TO_TARGET"});

    // 7. Open gripper
    trajectory.push_back({toX, toY, pickHeightZ_, GRIPPER_OPEN, "RELEASE_PIECE"});

    // 8. Retract to safe height
    trajectory.push_back({toX, toY, safeHeightZ_, GRIPPER_OPEN, "RETRACT"});

    return trajectory;
}

} // namespace ac::motion