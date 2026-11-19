#pragma once

#include <optional>
#include <vector>

#include "engine/stockfish_uci.hpp"
#include "motion/task_planner.hpp"

namespace ac::integration {

struct EngineTurnPlan {
    chess::engine::UciStatus engineStatus;
    std::optional<chess::Move> validatedMove;
    std::vector<motion::PhysicalTask> tasks;
};

// On UCI Success, an empty validatedMove means Chess Core rejected the proposal.
// Planning errors propagate from TaskPlanner. The logical board remains unchanged.
[[nodiscard]] EngineTurnPlan planEngineTurn(
    const chess::Board& board, chess::engine::StockfishUCI& engine,
    motion::TaskPlanner& planner, int depth);

} // namespace ac::integration
