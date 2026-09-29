#ifndef ACMOTION_PHYSICAL_TASK_HPP
#define ACMOTION_PHYSICAL_TASK_HPP

#include <optional>

#include "board/piece.hpp"
#include "board/square.hpp"
#include "motion/coordinate_mapper.hpp"

namespace ac::motion {

/**
 * @enum PhysicalTaskType
 * @brief High-level physical operations generated from one validated chess move.
 *
 * Physical tasks are executed on the Linux SBC side and are later expanded into
 * trajectories by MotionPlanner. They are not motor-driver commands and must
 * never be sent directly to STEP/DIR hardware.
 */
enum class PhysicalTaskType {
    MoveBoardPiece,      ///< Move one board piece from one board square to another.
    RemoveCapturedPiece, ///< Move a captured piece from the board into its graveyard.
    PromotionRequired    ///< Pawn reached the last rank and requires an explicit physical replacement strategy.
};

/**
 * @struct PhysicalTask
 * @brief Describes one high-level robot manipulation task.
 *
 * A task may reference both logical board coordinates and calibrated physical
 * coordinates. Optional fields are used because PromotionRequired is a control
 * task rather than a direct pick-and-place transfer.
 *
 * @invariant MoveBoardPiece and RemoveCapturedPiece contain both physical
 *            endpoints. PromotionRequired has no physical source because the
 *            replacement hardware and manipulation strategy are not defined.
 */
struct PhysicalTask {
    PhysicalTaskType type{PhysicalTaskType::MoveBoardPiece}; ///< Task category.
    ac::chess::Piece piece{};                                ///< Piece manipulated by this task.
    std::optional<ac::chess::Square> boardSource{};          ///< Logical source square when applicable.
    std::optional<ac::chess::Square> boardTarget{};          ///< Logical target square when applicable.
    std::optional<Point2D> physicalSource{};                 ///< Calibrated source coordinate in mm.
    std::optional<Point2D> physicalTarget{};                 ///< Calibrated target coordinate in mm.
};

} // namespace ac::motion

#endif
