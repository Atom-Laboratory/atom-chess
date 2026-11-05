#include "integration/board_move_adapter.hpp"

#include <stdexcept>

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

}
