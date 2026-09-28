#include "motion/motion_planner.hpp"

#include <cmath>
#include <stdexcept>

namespace ac::motion {

MotionPlanner::MotionPlanner(
    const CoordinateMapper& mapper,
    double safeHeightZ,
    double pickHeightZ)
    : mapper_(mapper),
      safeHeightZ_(safeHeightZ),
      pickHeightZ_(pickHeightZ)
{
    if (!std::isfinite(safeHeightZ_)
        || !std::isfinite(pickHeightZ_)
        || safeHeightZ_ <= pickHeightZ_) {
        throw std::invalid_argument(
            "safeHeightZ must be finite and greater than pickHeightZ"
        );
    }
}

void MotionPlanner::validatePoint(Point2D point)
{
    if (!std::isfinite(point.x) || !std::isfinite(point.y)) {
        throw std::invalid_argument("MotionPlanner point must be finite");
    }
}

std::vector<Pose> MotionPlanner::planTransfer(
    Point2D source,
    Point2D target) const
{
    validatePoint(source);
    validatePoint(target);

    return {
        {source.x, source.y, safeHeightZ_, GRIPPER_OPEN, "APPROACH_SOURCE"},
        {source.x, source.y, pickHeightZ_, GRIPPER_OPEN, "LOWER_TO_SOURCE"},
        {source.x, source.y, pickHeightZ_, GRIPPER_CLOSED, "GRASP_PIECE"},
        {source.x, source.y, safeHeightZ_, GRIPPER_CLOSED, "LIFT_PIECE"},
        {target.x, target.y, safeHeightZ_, GRIPPER_CLOSED, "APPROACH_TARGET"},
        {target.x, target.y, pickHeightZ_, GRIPPER_CLOSED, "LOWER_TO_TARGET"},
        {target.x, target.y, pickHeightZ_, GRIPPER_OPEN, "RELEASE_PIECE"},
        {target.x, target.y, safeHeightZ_, GRIPPER_OPEN, "RETRACT"}
    };
}

std::vector<Pose> MotionPlanner::planBoardMove(
    const std::string& from,
    const std::string& to) const
{
    return planTransfer(
        mapper_.boardSquare(from),
        mapper_.boardSquare(to)
    );
}

std::vector<Pose> MotionPlanner::planTask(
    const PhysicalTask& task) const
{
    switch (task.type) {
        case PhysicalTaskType::MoveBoardPiece:
        case PhysicalTaskType::RemoveCapturedPiece:
            if (!task.physicalSource.has_value()
                || !task.physicalTarget.has_value()) {
                throw std::invalid_argument(
                    "Physical transfer task requires source and target coordinates"
                );
            }
            return planTransfer(
                *task.physicalSource,
                *task.physicalTarget
            );

        case PhysicalTaskType::PromotionRequired:
            throw std::invalid_argument(
                "PromotionRequired has no physical replacement strategy"
            );
    }

    throw std::invalid_argument("Unsupported physical task type");
}

Pose MotionPlanner::getPredefinedPose(PredefinedPosition position) const
{
    switch (position) {
        case PredefinedPosition::HOME:
            return HOME_POSE;
        case PredefinedPosition::SAFE_STAGING:
            return SAFE_STAGING_POSE;
    }

    return HOME_POSE;
}

} // namespace ac::motion
