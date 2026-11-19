#include "integration/board_move_adapter.hpp"

#include <stdexcept>
#include <algorithm>
#include <cctype>

namespace ac::integration {
namespace {

std::string algebraic(chess::Square square)
{
    if (square.row < 0 || square.row > 7 || square.col < 0 || square.col > 7) {
        throw std::invalid_argument("Physical task square is outside the board");
    }
    return {static_cast<char>('a' + square.col), static_cast<char>('8' - square.row)};
}

}

BoardMoveRequest adaptBoardMove(std::span<const motion::PhysicalTask> plan)
{
    if (plan.size() != 1 || plan.front().type != motion::PhysicalTaskType::MoveBoardPiece) {
        throw std::invalid_argument("Only a single board transfer is supported");
    }
    const auto& task = plan.front();
    if (!task.boardSource || !task.boardTarget || task.boardSource == task.boardTarget) {
        throw std::invalid_argument("Two distinct board endpoints are required");
    }
    return {algebraic(*task.boardSource), algebraic(*task.boardTarget)};
}

std::string serializeBoardMove(std::span<const motion::PhysicalTask> plan)
{
    const auto request = adaptBoardMove(plan);
    // Both endpoints are generated from validated board indices, not raw input.
    return "{\"schema\":1,\"operation\":\"MOVE\",\"source\":\"" + request.source
        + "\",\"target\":\"" + request.target + "\"}";
}

std::string serializePhysicalPlan(std::span<const motion::PhysicalTask> plan,
                                  const GraveyardSlotResolver& resolveSlot)
{
    if (plan.empty() || plan.size() > 4) {
        throw std::invalid_argument("Unsupported plan size");
    }
    std::string result = R"({"schema":2,"operation":"PLAN","transfers":[)";
    for (const auto& task : plan) {
        if (!task.boardSource) throw std::invalid_argument("Source required");
        const auto source = algebraic(*task.boardSource);
        std::string target;
        if (task.type == motion::PhysicalTaskType::MoveBoardPiece) {
            if (!task.boardTarget || task.boardTarget == task.boardSource)
                throw std::invalid_argument("Distinct target required");
            target = algebraic(*task.boardTarget);
        } else if (task.type == motion::PhysicalTaskType::RemoveCapturedPiece) {
            if (!task.physicalTarget || !resolveSlot || task.boardTarget)
                throw std::invalid_argument("Explicit Graveyard mapping required");
            const auto slot = resolveSlot(*task.physicalTarget);
            if (slot.empty() || !std::all_of(slot.begin(), slot.end(), [](unsigned char c) {
                    return std::isalnum(c) || c == '_' || c == '-';
                })) throw std::invalid_argument("Invalid Graveyard slot name");
            target = "graveyard:" + slot;
        } else {
            throw std::invalid_argument("Promotion replacement is unsupported");
        }
        if (&task != &plan.front()) result += ',';
        result += "{\"source\":\"" + source + "\",\"target\":\"" + target + "\"}";
    }
    return result + "]}";
}

}
