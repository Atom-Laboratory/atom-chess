/**
 * @file motion_planner.cpp
 * @brief Implementation of the MotionPlanner trajectory generation methods.
 */

#include "motion/motion_planner.hpp"
#include <algorithm>
#include <stdexcept>

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
        case PredefinedPosition::GRAVEYARD_WHITE:
            return GRAVEYARD_WHITE_BASE;
        case PredefinedPosition::GRAVEYARD_BLACK:
            return GRAVEYARD_BLACK_BASE;
        case PredefinedPosition::SAFE_STAGING:
            return {0.0, 0.0, safeHeightZ_, GRIPPER_OPEN, "SAFE_STAGING"};
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

Pose MotionPlanner::getGraveyardSlotPose(PieceColor color, std::size_t slotIndex) const {
    if (slotIndex >= GRAVEYARD_CAPACITY) {
        throw std::out_of_range("Graveyard slot index exceeds maximum capacity of 16 (2x8 matrix).");
    }

    // Layout: 2 rows x 8 columns
    std::size_t row = slotIndex / 8;
    std::size_t col = slotIndex % 8;

    Pose base = (color == PieceColor::WHITE) ? GRAVEYARD_WHITE_BASE : GRAVEYARD_BLACK_BASE;

    // Calculate grid displacement
    double targetX = base.x + (col * SLOT_SPACING_X);
    double targetY = base.y + (row * SLOT_SPACING_Y);

    std::string label = (color == PieceColor::WHITE ? "GRAVEYARD_WHITE_SLOT_" : "GRAVEYARD_BLACK_SLOT_") 
                      + std::to_string(slotIndex);

    return {targetX, targetY, base.z, base.gripper_percent, label};
}

Pose MotionPlanner::allocateNextGraveyardPose(PieceColor color) {
    std::size_t& index = (color == PieceColor::WHITE) ? white_graveyard_index_ : black_graveyard_index_;

    if (index >= GRAVEYARD_CAPACITY) {
        throw std::out_of_range("Graveyard matrix is fully occupied.");
    }

    Pose allocatedPose = getGraveyardSlotPose(color, index);
    index++; // Advance to the next free slot
    return allocatedPose;
}

void MotionPlanner::resetGraveyards() {
    white_graveyard_index_ = 0;
    black_graveyard_index_ = 0;
}

} // namespace ac::motion