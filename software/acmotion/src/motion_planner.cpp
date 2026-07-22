#include "motion/motion_planner.hpp"

namespace ac {

MotionPlanner::MotionPlanner(const CoordinateMapperMock& mapper, 
                             double safeHeightZ, 
                             double pickHeightZ)
    : mapper_(mapper), safeHeightZ_(safeHeightZ), pickHeightZ_(pickHeightZ) {}

std::vector<Pose> MotionPlanner::planMove(const std::string& fromSquare, const std::string& toSquare) const {
    std::vector<Pose> trajectory;

    auto [x1, y1] = mapper_.getCoordinates(fromSquare);
    auto [x2, y2] = mapper_.getCoordinates(toSquare);

    // 1. Posição Inicial de Segurança (HOME)
    trajectory.push_back(HOME_POSE);

    // 2. Sequência na Origem (Aproxima, Pega, Eleva)
    trajectory.push_back({x1, y1, safeHeightZ_, GripperState::OPEN,   fromSquare + "_APPROACH"});
    trajectory.push_back({x1, y1, pickHeightZ_,  GripperState::CLOSED, fromSquare + "_PICK"});
    trajectory.push_back({x1, y1, safeHeightZ_, GripperState::CLOSED, fromSquare + "_LIFT"});

    // 3. Sequência no Destino (Aproxima, Solta, Eleva)
    trajectory.push_back({x2, y2, safeHeightZ_, GripperState::CLOSED, toSquare + "_APPROACH"});
    trajectory.push_back({x2, y2, pickHeightZ_,  GripperState::OPEN,   toSquare + "_PLACE"});
    trajectory.push_back({x2, y2, safeHeightZ_, GripperState::OPEN,   toSquare + "_RELEASE"});

    // 4. Retorno Seguro para Repouso
    trajectory.push_back(HOME_POSE);

    return trajectory;
}

} // namespace ac