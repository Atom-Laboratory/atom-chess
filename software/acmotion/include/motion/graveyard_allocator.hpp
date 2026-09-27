#ifndef ACMOTION_GRAVEYARD_ALLOCATOR_HPP
#define ACMOTION_GRAVEYARD_ALLOCATOR_HPP

#include <cstddef>
#include <map>
#include <utility>

#include "board/piece.hpp"
#include "motion/coordinate_mapper.hpp"

namespace ac::motion {

/**
 * @class GraveyardAllocator
 * @brief Allocates captured chess pieces to deterministic physical graveyard slots.
 *
 * This is high-level Motion logic for the Linux SBC. It consumes the
 * authoritative ac::chess::Piece model, chooses a logical 2x8 graveyard slot,
 * and delegates physical XY conversion to CoordinateMapper.
 *
 * The ESP32-S3 receives already planned motion targets and does not own chess
 * piece state or graveyard allocation policy.
 *
 * Logical layout per color:
 * - row 0: eight pawn slots;
 * - row 1: two rooks, two knights, two bishops, one queen, one king.
 */
class GraveyardAllocator {
public:
    /**
     * @brief Creates an allocator backed by a calibrated CoordinateMapper.
     * @param mapper Coordinate mapper used to resolve physical graveyard slots.
     * @note The mapper must outlive this allocator.
     */
    explicit GraveyardAllocator(const CoordinateMapper& mapper);

    /**
     * @brief Allocates the next free slot for a captured piece.
     * @param piece Captured non-empty chess piece.
     * @return Calibrated XY position in the robot reference frame.
     * @throws std::invalid_argument when piece is empty or invalid.
     * @throws std::out_of_range when the piece-type capacity is exhausted.
     */
    Point2D allocateNext(const ac::chess::Piece& piece);
    /**
     * @brief Resolves a logical graveyard slot without consuming it.
     * @param color Captured-piece color.
     * @param type Captured-piece type.
     * @param indexInType Zero-based index inside the type-specific capacity.
     * @return Calibrated XY position in the robot reference frame.
     * @throws std::invalid_argument when color/type is unsupported.
     * @throws std::out_of_range when indexInType exceeds the type capacity.
     * @throws std::runtime_error when the corresponding graveyard geometry
     *         is not configured in CoordinateMapper.
     */
    Point2D slotFor(
        ac::chess::PieceColor color,
        ac::chess::PieceType type,
        std::size_t indexInType
    ) const;

    /**
     * @brief Clears logical occupation counters for a new game.
     *
     * Physical calibration stored in CoordinateMapper is preserved.
     */
    void reset();

private:
    /**
     * @brief Returns the number of physical slots reserved for a piece type.
     * @param type Concrete chess piece type.
     * @return Capacity reserved for the type.
     * @throws std::invalid_argument for PieceType::None or unsupported values.
     */
    static std::size_t capacityFor(ac::chess::PieceType type);
    /**
     * @brief Maps a type-specific allocation index to the logical 2x8 grid.
     * @param type Concrete chess piece type.
     * @param indexInType Zero-based allocation index for that type.
     * @return Pair containing logical row and column.
     * @throws std::invalid_argument for unsupported types.
     * @throws std::out_of_range when indexInType exceeds type capacity.
     */
    static std::pair<std::size_t, std::size_t> gridPosition(
        ac::chess::PieceType type,
        std::size_t indexInType
    );

    /**
     * @brief Maps chess color to the corresponding calibrated graveyard side.
     * @param color White or Black.
     * @return Physical graveyard side used by CoordinateMapper.
     * @throws std::invalid_argument for PieceColor::None.
     */
    static GraveyardSide sideFor(ac::chess::PieceColor color);

    const CoordinateMapper& mapper_; ///< Source of calibrated physical coordinates.

    std::map<
        std::pair<ac::chess::PieceColor, ac::chess::PieceType>,
        std::size_t
    > counts_;
};

} // namespace ac::motion

#endif
