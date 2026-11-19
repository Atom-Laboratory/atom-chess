#include "integration/engine_turn_planner.hpp"

#include "board/move_validator.hpp"
#include "fen_generator/fen_generator.hpp"

namespace ac::integration {

EngineTurnPlan planEngineTurn(
    const chess::Board& board, chess::engine::StockfishUCI& engine,
    motion::TaskPlanner& planner, int depth)
{
    const auto response = engine.request_best_move(chess::FenGenerator::generate(board), depth);
    EngineTurnPlan plan{response.status, std::nullopt, {}};
    if (response.status == chess::engine::UciStatus::Success) {
        plan.validatedMove = chess::MoveValidator::validateUci(board, response.move);
        if (plan.validatedMove) {
            plan.tasks = planner.planTasks(board, *plan.validatedMove);
        }
    }
    return plan;
}

} // namespace ac::integration
