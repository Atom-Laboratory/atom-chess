#include <gtest/gtest.h>

#include <cstdio>

#include "motion/coordinate_mapper.hpp"

using ac::motion::CoordinateMapper;
using ac::motion::GraveyardSide;
using ac::motion::GridGeometry;
using ac::motion::Point2D;
using ac::motion::RankDirection;

TEST(CoordinateMapperTest, MapsBoardSquaresWithoutLookupTable)
{
    CoordinateMapper mapper("");
    mapper.calibrateBoard({100.0, 200.0}, {450.0, 200.0});

    const Point2D a1 = mapper.boardSquare("A1");
    const Point2D h1 = mapper.boardSquare("h1");
    const Point2D a8 = mapper.boardSquare("A8");

    EXPECT_DOUBLE_EQ(a1.x, 100.0);
    EXPECT_DOUBLE_EQ(a1.y, 200.0);
    EXPECT_NEAR(h1.x, 450.0, 1e-9);
    EXPECT_NEAR(h1.y, 200.0, 1e-9);
    EXPECT_NEAR(a8.x, 100.0, 1e-9);
    EXPECT_NEAR(a8.y, 550.0, 1e-9);
}

TEST(CoordinateMapperTest, SupportsClockwiseRankAxis)
{
    CoordinateMapper mapper("");
    mapper.calibrateBoard(
        {0.0, 0.0},
        {70.0, 0.0},
        RankDirection::CLOCKWISE
    );

    const Point2D a2 = mapper.boardSquare("A2");
    EXPECT_NEAR(a2.x, 0.0, 1e-9);
    EXPECT_NEAR(a2.y, -10.0, 1e-9);
}

TEST(CoordinateMapperTest, RejectsInvalidSquare)
{
    CoordinateMapper mapper("");
    mapper.calibrateBoard({0.0, 0.0}, {70.0, 0.0});

    EXPECT_THROW(mapper.boardSquare("I9"), std::invalid_argument);
    EXPECT_THROW(mapper.boardSquare("A10"), std::invalid_argument);
}

TEST(CoordinateMapperTest, MapsGraveyardGridInRobotFrame)
{
    CoordinateMapper mapper("");

    GridGeometry geometry;
    geometry.origin = {500.0, -100.0};
    geometry.columnStep = {30.0, 0.0};
    geometry.rowStep = {0.0, 35.0};
    geometry.rows = 2;
    geometry.columns = 8;

    mapper.setGraveyardGeometry(GraveyardSide::WHITE, geometry);

    const Point2D slot = mapper.graveyardSlot(
        GraveyardSide::WHITE,
        1,
        7
    );

    EXPECT_DOUBLE_EQ(slot.x, 710.0);
    EXPECT_DOUBLE_EQ(slot.y, -65.0);
    EXPECT_THROW(
        mapper.graveyardSlot(GraveyardSide::WHITE, 2, 0),
        std::out_of_range
    );
}

TEST(CoordinateMapperTest, PersistsBoardCalibration)
{
    const char* path = "coordinate_mapper_test.cfg";

    {
        CoordinateMapper mapper(path);
        mapper.calibrateBoard({10.0, 20.0}, {80.0, 20.0});
    }

    {
        CoordinateMapper mapper(path);
        ASSERT_TRUE(mapper.isBoardCalibrated());
        const Point2D b2 = mapper.boardSquare("B2");
        EXPECT_NEAR(b2.x, 20.0, 1e-9);
        EXPECT_NEAR(b2.y, 30.0, 1e-9);
    }

    EXPECT_EQ(std::remove(path), 0);
}
