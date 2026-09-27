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
    Point2D slotFor(
        ac::chess::PieceColor color,
        ac::chess::PieceType type,
        std::size_t indexInType
    ) const;

    void reset();

private:
    static std::size_t capacityFor(ac::chess::PieceType type);
    static std::pair<std::size_t, std::size_t> gridPosition(
        ac::chess::PieceType type,
        std::size_t indexInType
    );
    static GraveyardSide sideFor(ac::chess::PieceColor color);

    const CoordinateMapper& mapper_;

    std::map<
        std::pair<ac::chess::PieceColor, ac::chess::PieceType>,
        std::size_t
    > counts_;
};

} // namespace ac::motion

#endif
