#include <gtest/gtest.h>
#include <stdexcept>
#include "../include/motion/motion_planner.hpp"

using namespace ac::motion;

class MotionPlannerTest : public ::testing::Test {
protected:
    CoordinateMapperMock mapper;
    MotionPlanner planner{mapper, 50.0, 10.0};
};

TEST_F(MotionPlannerTest, GraveyardAllocationTypeSeparation) {
    // Alocar um Peão Branco não deve consumir o slot de uma Torre Branca
    Pose pawnPose = planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn);
    Pose rookPose = planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Rook);

    // Peões ficam na linha 0 e Torres na linha 1 (diferentes posições Y)
    EXPECT_NE(pawnPose.y, rookPose.y);

    // Preencher o limite máximo de peões brancos (8 peões)
    for (int i = 0; i < 7; ++i) {
        EXPECT_NO_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn));
    }

    // O 9º peão deve lançar exceção out_of_range
    EXPECT_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn), std::out_of_range);

    // Mas ainda deve ser possível alocar a segunda Torre Branca normalmente
    EXPECT_NO_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Rook));
}

TEST_F(MotionPlannerTest, GraveyardColorIndependence) {
    // A alocação de peças brancas e pretas deve ser independente
    Pose whitePawn = planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn);
    Pose blackPawn = planner.allocateNextGraveyardPose(PieceColor::Black, PieceType::Pawn);

    // As coordenadas X devem ser opostas/distintas devido às bases diferentes
    EXPECT_NE(whitePawn.x, blackPawn.x);
}

TEST_F(MotionPlannerTest, InvalidPieceTypeHandling) {
    // Tentar alocar peça sem cor ou sem tipo deve lançar invalid_argument
    EXPECT_THROW(planner.allocateNextGraveyardPose(PieceColor::None, PieceType::Pawn), std::invalid_argument);
    EXPECT_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::None), std::invalid_argument);
}

TEST_F(MotionPlannerTest, ResetGraveyard) {
    // Encher peões brancos até o limite
    for (int i = 0; i < 8; ++i) {
        planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn);
    }
    EXPECT_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn), std::out_of_range);

    // Após o reset, deve ser possível alocar novamente
    planner.resetGraveyards();
    EXPECT_NO_THROW(planner.allocateNextGraveyardPose(PieceColor::White, PieceType::Pawn));
}