#pragma once

#include <span>
#include <string>

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

}
