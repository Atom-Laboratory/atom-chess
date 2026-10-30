#include "motion/graveyard_allocator.hpp"

#include <stdexcept>

namespace ac::motion {

/**
 * @brief Binds allocation policy to the calibrated coordinate mapper.
 */
GraveyardAllocator::GraveyardAllocator(const CoordinateMapper& mapper)
    : mapper_(mapper)
{
}

/**
 * @brief Returns the fixed slot capacity reserved for a chess piece type.
 */
std::size_t GraveyardAllocator::capacityFor(ac::chess::PieceType type)
{
    switch (type) {
        case ac::chess::PieceType::Pawn:   return 8;
        case ac::chess::PieceType::Rook:   return 2;
        case ac::chess::PieceType::Knight: return 2;
        case ac::chess::PieceType::Bishop: return 2;
        case ac::chess::PieceType::Queen:  return 1;
        case ac::chess::PieceType::King:   return 1;
        case ac::chess::PieceType::None:
            break;
    }

    throw std::invalid_argument("Unsupported piece type for graveyard allocation");
}

/**
 * @brief Maps a type-relative capture index into the shared logical 2x8 grid.
 */
std::pair<std::size_t, std::size_t> GraveyardAllocator::gridPosition(
    ac::chess::PieceType type,
    std::size_t indexInType)
{
    const std::size_t capacity = capacityFor(type);
    if (indexInType >= capacity) {
        throw std::out_of_range("Graveyard capacity exceeded for piece type");
    }

    switch (type) {
        case ac::chess::PieceType::Pawn:
            return {0, indexInType};
        case ac::chess::PieceType::Rook:
            return {1, indexInType};
        case ac::chess::PieceType::Knight:
            return {1, 2 + indexInType};
        case ac::chess::PieceType::Bishop:
            return {1, 4 + indexInType};
        case ac::chess::PieceType::Queen:
            return {1, 6};
        case ac::chess::PieceType::King:
            return {1, 7};
        case ac::chess::PieceType::None:
            break;
    }

    throw std::invalid_argument("Unsupported piece type for graveyard allocation");
}

/**
 * @brief Converts chess color into the corresponding physical graveyard side.
 */
GraveyardSide GraveyardAllocator::sideFor(ac::chess::PieceColor color)
{
    switch (color) {
        case ac::chess::PieceColor::White:
            return GraveyardSide::WHITE;
        case ac::chess::PieceColor::Black:
            return GraveyardSide::BLACK;
        case ac::chess::PieceColor::None:
            break;
    }

    throw std::invalid_argument("Piece color must be White or Black");
}

/**
 * @brief Resolves a non-consuming type-specific slot to calibrated physical XY.
 */
Point2D GraveyardAllocator::slotFor(
    ac::chess::PieceColor color,
    ac::chess::PieceType type,
    std::size_t indexInType) const
{
    const auto [row, column] = gridPosition(type, indexInType);
    return mapper_.graveyardSlot(sideFor(color), row, column);
}

/**
 * @brief Reserves and returns the next slot for a concrete captured piece.
 *
 * The allocation counter advances only after CoordinateMapper resolves the
 * target successfully.
 */
Point2D GraveyardAllocator::allocateNext(const ac::chess::Piece& piece)
{
    if (!ac::chess::isValid(piece)
        || piece.type == ac::chess::PieceType::None) {
        throw std::invalid_argument("Captured piece must have a concrete type and color");
    }

    const auto key = std::make_pair(piece.color, piece.type);
    const std::size_t index = counts_[key];

    if (index >= capacityFor(piece.type)) {
        throw std::out_of_range("Graveyard capacity exceeded for piece type");
    }

    const Point2D target = slotFor(piece.color, piece.type, index);
    ++counts_[key];
    return target;
}

/**
 * @brief Releases all logical graveyard reservations for a new game.
 */
void GraveyardAllocator::reset()
{
    counts_.clear();
}

} // namespace ac::motion
