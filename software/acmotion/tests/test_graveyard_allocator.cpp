#include <gtest/gtest.h>

#include "board/piece.hpp"
#include "motion/coordinate_mapper.hpp"
#include "motion/graveyard_allocator.hpp"

namespace ac::motion {

TEST(GraveyardAllocatorTest, AllocatesByTypeColorAndCapacity)
{
    CoordinateMapper mapper("");

    GridGeometry white{{200.0, -100.0}, {20.0, 0.0}, {0.0, 20.0}, 2, 8};
    GridGeometry black{{-200.0, -100.0}, {-20.0, 0.0}, {0.0, 20.0}, 2, 8};

    mapper.setGraveyardGeometry(GraveyardSide::WHITE, white);
    mapper.setGraveyardGeometry(GraveyardSide::BLACK, black);

    GraveyardAllocator allocator(mapper);

    const auto pawn = allocator.allocateNext(
        {ac::chess::PieceType::Pawn, ac::chess::PieceColor::White}
    );
    const auto rook = allocator.allocateNext(
        {ac::chess::PieceType::Rook, ac::chess::PieceColor::White}
    );
    const auto blackPawn = allocator.allocateNext(
        {ac::chess::PieceType::Pawn, ac::chess::PieceColor::Black}
    );

    EXPECT_NE(pawn.y, rook.y);
    EXPECT_NE(pawn.x, blackPawn.x);

    for (int i = 1; i < 8; ++i) {
        allocator.allocateNext(
            {ac::chess::PieceType::Pawn, ac::chess::PieceColor::White}
        );
    }

    EXPECT_THROW(
        allocator.allocateNext(
            {ac::chess::PieceType::Pawn, ac::chess::PieceColor::White}
        ),
        std::out_of_range
    );

    allocator.reset();
    EXPECT_NO_THROW(allocator.allocateNext(
        {ac::chess::PieceType::Pawn, ac::chess::PieceColor::White}
    ));
}

} // namespace ac::motion
