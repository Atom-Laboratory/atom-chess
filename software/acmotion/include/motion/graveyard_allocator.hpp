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
 * This is high-level Motion logic for the Linux SBC. The ESP32-S3 receives
 * already planned coordinates/trajectories and does not own chess piece state.
 */
class GraveyardAllocator {
public:
    explicit GraveyardAllocator(const CoordinateMapper& mapper);

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
