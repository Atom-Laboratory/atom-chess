#include <gtest/gtest.h>

#include "board/board.hpp"
#include "board_observation/board_observation.hpp"
#include "integration/observation_interpreter.hpp"

using namespace ac;
using namespace ac::integration;

TEST(ObservationInterpreterTest, DetectsNoChangeWhenObservationsAreEqual) {
    chess::Board board;
    BoardObservation prev{};
    BoardObservation curr{};

    auto result = interpretObservation(board, prev, curr);

    EXPECT_EQ(result.status, ObservationValidationResult::Status::NoChange);
    EXPECT_FALSE(result.move.has_value());
}