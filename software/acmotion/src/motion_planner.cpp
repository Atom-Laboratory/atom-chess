#include "motion/motion_planner.hpp"
#include <stdexcept>
#include <algorithm>

namespace ac::motion {

MotionPlanner::MotionPlanner(const CoordinateMapperMock& mapper, 
                             double safeHeightZ, 
                             double pickHeightZ)
    : mapper_(mapper), safeHeightZ_(safeHeightZ), pickHeightZ_(pickHeightZ) {
    resetGraveyards();
}

void MotionPlanner::resetGraveyards() {
    graveyard_counts_.clear();
}

std::size_t MotionPlanner::getMaxCapacityForType(PieceType type) {
    switch (type) {
        case PieceType::Pawn:   return 8;
        case PieceType::Rook:   return 2;
        case PieceType::Knight: return 2;
        case PieceType::Bishop: return 2;
        case PieceType::Queen:  return 1;
        case PieceType::King:   return 1;
        default:
            throw std::invalid_argument("Tipo de peca invalido ou nao suportado no Graveyard.");
    }
}

std::pair<std::size_t, std::size_t> MotionPlanner::getSlotGridPosition(PieceType type, std::size_t indexInType) {
    std::size_t maxCap = getMaxCapacityForType(type);
    if (indexInType >= maxCap) {
        throw std::out_of_range("Indice de peca excede a capacidade maxima permitida para este tipo.");
    }

    // Linha 0 (8 slots): Peões (Pawn)
    // Linha 1 (8 slots): Peças Nobres (Rook, Knight, Bishop, Queen, King)
    switch (type) {
        case PieceType::Pawn:
            return {0, indexInType}; // Colunas 0 a 7
        case PieceType::Rook:
            return {1, indexInType}; // Colunas 0 e 1
        case PieceType::Knight:
            return {1, 2 + indexInType}; // Colunas 2 e 3
        case PieceType::Bishop:
            return {1, 4 + indexInType}; // Colunas 4 e 5
        case PieceType::Queen:
            return {1, 6}; // Coluna 6
        case PieceType::King:
            return {1, 7}; // Coluna 7
        default:
            throw std::invalid_argument("Tipo de peca invalido.");
    }
}

Pose MotionPlanner::getGraveyardSlotPose(PieceColor color, PieceType type, std::size_t indexInType) const {
    if (color == PieceColor::None || type == PieceType::None) {
        throw std::invalid_argument("Cor e Tipo de peca devem ser validos.");
    }

    auto [row, col] = getSlotGridPosition(type, indexInType);

    // Define a pose base de acordo com a cor
    Pose basePose = (color == PieceColor::White) ? GRAVEYARD_WHITE_BASE : GRAVEYARD_BLACK_BASE;

    // Aplica os offsets espaciais da matriz 2x8
    basePose.x += (col * SLOT_SPACING_X);
    basePose.y += (row * SLOT_SPACING_Y);
    basePose.label = "GRAVEYARD_SLOT_" + std::to_string(row) + "_" + std::to_string(col);

    return basePose;
}

Pose MotionPlanner::allocateNextGraveyardPose(PieceColor color, PieceType type) {
    if (color == PieceColor::None || type == PieceType::None) {
        throw std::invalid_argument("Cor e Tipo de peca devem ser validos.");
    }

    auto key = std::make_pair(color, type);
    std::size_t currentIndex = graveyard_counts_[key];
    std::size_t maxCap = getMaxCapacityForType(type);

    if (currentIndex >= maxCap) {
        throw std::out_of_range("Graveyard cheio para este tipo de peca especifico.");
    }

    Pose pose = getGraveyardSlotPose(color, type, currentIndex);
    graveyard_counts_[key]++; // Incrementa o contador apenas daquele par (Cor, Tipo)
    
    return pose;
}

Pose MotionPlanner::getPredefinedPose(PredefinedPosition pos) const {
    switch (pos) {
        case PredefinedPosition::HOME:
            return HOME_POSE;
        case PredefinedPosition::GRAVEYARD:
            return GRAVEYARD_POSE;
        case PredefinedPosition::GRAVEYARD_WHITE:
            return GRAVEYARD_WHITE_BASE;
        case PredefinedPosition::GRAVEYARD_BLACK:
            return GRAVEYARD_BLACK_BASE;
        case PredefinedPosition::SAFE_STAGING:
            return {0.0, 0.0, safeHeightZ_, GRIPPER_OPEN, "SAFE_STAGING"};
        default:
            throw std::invalid_argument("Posicao predefinida desconhecida.");
    }
}

std::vector<Pose> MotionPlanner::planMove(const std::string& from, const std::string& to) {
    auto [fromX, fromY] = mapper_.getCoordinates(from);
    auto [toX, toY]     = mapper_.getCoordinates(to);

    std::vector<Pose> trajectory;

    // 1. Deslocamento para posicao segura sobre a origem
    trajectory.push_back({fromX, fromY, safeHeightZ_, GRIPPER_OPEN, "APPROACH_SOURCE"});
    // 2. Descida para pegar a peca
    trajectory.push_back({fromX, fromY, pickHeightZ_, GRIPPER_CLOSED, "PICK_PIECE"});
    // 3. Subida com a peca presa
    trajectory.push_back({fromX, fromY, safeHeightZ_, GRIPPER_CLOSED, "LIFT_PIECE"});
    // 4. Deslocamento horizontal seguro para o destino
    trajectory.push_back({toX, toY, safeHeightZ_, GRIPPER_CLOSED, "APPROACH_TARGET"});
    // 5. Descida para soltar a peca
    trajectory.push_back({toX, toY, pickHeightZ_, GRIPPER_OPEN, "RELEASE_PIECE"});
    // 6. Retorno para altura de seguranca
    trajectory.push_back({toX, toY, safeHeightZ_, GRIPPER_OPEN, "RETRACT"});

    return trajectory;
}

} // namespace ac::motion