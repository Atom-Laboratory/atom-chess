#pragma once

#include <span>
#include <string>
#include <functional>

#include "motion/physical_task.hpp"

namespace ac::integration {

struct BoardMoveRequest {
    std::string source;
    std::string target;
};

// Convert a complete, already planned Chess Core operation. Throws for plans
// outside the currently supported single board-transfer subset.
[[nodiscard]] BoardMoveRequest adaptBoardMove(
    std::span<const motion::PhysicalTask> plan
);

// Versioned JSON accepted by the MuJoCo Playground request consumer.
[[nodiscard]] std::string serializeBoardMove(std::span<const motion::PhysicalTask> plan);

// Caller maps calibrated robot-base XY (mm) to configured simulation/hardware slots.
using GraveyardSlotResolver = std::function<std::string(motion::Point2D)>;
[[nodiscard]] std::string serializePhysicalPlan(
    std::span<const motion::PhysicalTask> plan, const GraveyardSlotResolver& resolveSlot);

}
