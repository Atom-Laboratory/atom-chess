#ifndef ACMOTION_MOTION_PLANNER_HPP
#define ACMOTION_MOTION_PLANNER_HPP

#include <string>
#include <vector>
#include <utility>
#include <cstddef>
#include <map>

// Inclui a definição oficial de Piece, PieceType e PieceColor do módulo acchess
#include "../../acchess/include/board/piece.hpp"

/**
 * @file motion_planner.hpp
 * @brief Trajectory planning and motion execution interface for the SCARA robot.
 */

namespace ac::motion {

/**
 * @enum PredefinedPosition
 * @brief Predefined target positions for state machine transitions.
 */
enum class PredefinedPosition {
    HOME,
    GRAVEYARD,         ///< Legacy generic graveyard position
    GRAVEYARD_WHITE,   ///< Base position for white pieces 2x8 graveyard matrix
    GRAVEYARD_BLACK,   ///< Base position for black pieces 2x8 graveyard matrix
    SAFE_STAGING
};

/**
 * @struct Pose
 * @brief Represents a 3D Cartesian position, gripper aperture percentage, and debug label.
 */
struct Pose {
    double x{0.0};              ///< X-coordinate in mm
    double y{0.0};              ///< Y-coordinate in mm
    double z{0.0};              ///< Z-coordinate in mm
    double gripper_percent{0.0}; ///< Gripper opening percentage (0.0 = fully closed, 100.0 = fully open)
    std::string label;          ///< Descriptive tag for debugging and logging
};

/**
 * @class CoordinateMapperMock
 * @brief Mock implementation of the CoordinateMapper interface for board cell translation during testing.
 */
class CoordinateMapperMock {
public:
    virtual ~CoordinateMapperMock() = default;

    /**
     * @param square Algebraic notation string for the board cell.
     * @return std::pair<double, double> Cartesian coordinates {X, Y} in mm at table surface height (Z=0).
     */
    virtual std::pair<double, double> getCoordinates(const std::string& square) const {
        (void)square;
        return {100.0, 100.0}; // Simulated fixed coordinates
    }
};

/**
 * @class MotionPlanner
 * @brief Generates high-level sequential trajectories (poses) for chess piece manipulation.
 */
class MotionPlanner {
public:
    /**
     * @brief Constructs a MotionPlanner instance.
     * @param mapper Reference to the coordinate mapper interface.
     * @param safeHeightZ Clearance height in Z (mm) to avoid collisions.
     * @param pickHeightZ Height in Z (mm) for gripping/releasing pieces.
     */
    MotionPlanner(const CoordinateMapperMock& mapper, 
                  double safeHeightZ = 50.0, 
                  double pickHeightZ = 10.0);

    /**
     * @brief Generates a trajectory to move a piece from source cell to target cell.
     * @param from Algebraic notation of the starting square (e.g., "e2").
     * @param to Algebraic notation of the destination square (e.g., "e4").
     * @return std::vector<Pose> Sequence of 3D poses defining the pick-and-place movement.
     */
    std::vector<Pose> planMove(const std::string& from, const std::string& to);

    /**
     * @brief Returns a predefined pose based on the state machine Enum.
     * @param pos Desired predefined position.
     * @return Pose Cartesian pose associated with the predefined position.
     */
    Pose getPredefinedPose(PredefinedPosition pos) const;

    /**
     * @brief Gets the pose for a specific piece type and index in the graveyard matrix.
     * @param color Color of the captured piece (PieceColor::White or PieceColor::Black).
     * @param type Type of the piece (PieceType::Pawn, PieceType::Rook, etc.).
     * @param indexInType Sub-index for that specific piece type (0 to max capacity for type).
     */
    Pose getGraveyardSlotPose(PieceColor color, PieceType type, std::size_t indexInType) const;

    /**
     * @brief Plans a capture trajectory, sending the captured piece to the next free graveyard slot of its type.
     * @param color Color of the captured piece.
     * @param type Type of the captured piece.
     */
    Pose allocateNextGraveyardPose(PieceColor color, PieceType type);

    /**
     * @brief Overload accepting a full Piece struct for convenience.
     */
    Pose allocateNextGraveyardPose(const Piece& piece) {
        return allocateNextGraveyardPose(piece.color, piece.type);
    }

    /**
     * @brief Resets graveyard occupation indices for all piece types.
     */
    void resetGraveyards();

private:
    static std::size_t getMaxCapacityForType(PieceType type);
    static std::pair<std::size_t, std::size_t> getSlotGridPosition(PieceType type, std::size_t indexInType);

    const CoordinateMapperMock& mapper_;
    double safeHeightZ_;
    double pickHeightZ_;

    // Controle de ocupação por pares (Cor, Tipo de Peça)
    std::map<std::pair<PieceColor, PieceType>, std::size_t> graveyard_counts_;

    static constexpr double GRIPPER_OPEN = 100.0;
    static constexpr double GRIPPER_CLOSED = 0.0;

    const Pose HOME_POSE = {0.0, 0.0, 150.0, GRIPPER_OPEN, "HOME"};
    const Pose GRAVEYARD_POSE = {200.0, -100.0, 50.0, GRIPPER_OPEN, "GRAVEYARD"};
    const Pose GRAVEYARD_WHITE_BASE = {200.0, -100.0, 50.0, GRIPPER_OPEN, "GRAVEYARD_WHITE"};
    const Pose GRAVEYARD_BLACK_BASE = {-200.0, -100.0, 50.0, GRIPPER_OPEN, "GRAVEYARD_BLACK"};

    static constexpr double SLOT_SPACING_X = 20.0;
    static constexpr double SLOT_SPACING_Y = 20.0;
};

} // namespace ac::motion

#endif // ACMOTION_MOTION_PLANNER_HPP