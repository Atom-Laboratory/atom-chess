#ifndef ACMOTION_TASK_PLANNER_HPP
#define ACMOTION_TASK_PLANNER_HPP

#include <string>
#include <vector>

#include "board/board.hpp"
#include "board/move.hpp"
#include "motion/coordinate_mapper.hpp"
#include "motion/graveyard_allocator.hpp"
#include "motion/physical_task.hpp"

namespace ac::motion {

/**
 * @class TaskPlanner
 * @brief Converts one validated chess move into ordered physical manipulation tasks.
 *
 * TaskPlanner is the semantic boundary between Chess Core and geometric motion
 * planning. It runs on the Linux SBC/Brain and never emits stepper pulses,
 * accesses GPIO, or communicates directly with motor drivers.
 *
 * @par Responsibility split
 * - MoveValidator decides whether a move is legal.
 * - TaskPlanner decides which physical pieces must be moved and in what order.
 * - CoordinateMapper resolves board/graveyard positions in the SCARA base frame.
 * - GraveyardAllocator reserves deterministic slots for captured pieces.
 * - MotionPlanner converts each transfer task into collision-aware poses.
 * - ESP32-S3 executes low-level deterministic motion.
 *
 * @note planTasks() assumes the supplied Move has already been validated against
 *       boardBeforeMove. Structural inconsistencies are treated as programming
 *       errors and reported through exceptions instead of re-running chess rules.
 */
class TaskPlanner {
public:
    /**
     * @brief Creates a planner using calibrated board/graveyard geometry.
     * @param mapper Coordinate mapper used for board-square positions.
     * @param graveyardAllocator Allocator used to reserve captured-piece destinations.
     * @note Both referenced objects must outlive this planner.
     */
    TaskPlanner(
        const CoordinateMapper& mapper,
        GraveyardAllocator& graveyardAllocator
    );

    /**
     * @brief Expands one validated move into an ordered list of physical tasks.
     * @param boardBeforeMove Authoritative Board before the move is applied.
     * @param move Previously validated chess move.
     * @return Ordered tasks that preserve capture/special-move sequencing.
     *
     * @throws std::invalid_argument when move.from is empty, when capture flags
     *         contradict boardBeforeMove, or when a required piece is missing.
     * @throws std::out_of_range when GraveyardAllocator has no free slot.
     * @throws std::runtime_error when board/graveyard geometry is not calibrated.
     *
     * @post boardBeforeMove is never modified.
     * @post GraveyardAllocator consumes a slot only for actual captured pieces.
     */
    [[nodiscard]] std::vector<PhysicalTask> planTasks(
        const ac::chess::Board& boardBeforeMove,
        const ac::chess::Move& move
    );

private:
    /**
     * @brief Converts an internal zero-based Square to algebraic notation.
     * @param square Valid board square.
     * @return Two-character notation such as "e4".
     * @throws std::out_of_range when square is outside the board.
     */
    static std::string toAlgebraic(ac::chess::Square square);

    /**
     * @brief Resolves one board square to a calibrated SCARA XY point.
     * @param square Valid board square.
     * @return Physical coordinate in millimetres.
     */
    Point2D boardPoint(ac::chess::Square square) const;

    const CoordinateMapper& mapper_;          ///< Calibrated board coordinate source.
    GraveyardAllocator& graveyardAllocator_;  ///< Mutable captured-piece slot allocator.
};

} // namespace ac::motion

#endif
