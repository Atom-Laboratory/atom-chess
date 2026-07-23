#ifndef MOTION_PLANNER_HPP
#define MOTION_PLANNER_HPP

#include <string>
#include <vector>
#include <utility>

namespace ac {

// Estado da Garra do Robô
enum class GripperState {
    OPEN,
    CLOSED
};

// Estrutura para representar um Ponto/Pose no espaço 3D
struct Pose {
    double x;
    double y;
    double z;
    GripperState gripper;
    std::string label;
};

// Interface/Mock do CoordinateMapper (para testes enquanto a equipe desenvolve o oficial)
class CoordinateMapperMock {
public:
    virtual ~CoordinateMapperMock() = default;
    virtual std::pair<double, double> getCoordinates(const std::string& square) const {
        return {100.0, 100.0}; // Retorno estático simulado
    }
};

// Classe Principal do Planejador de Movimento
class MotionPlanner {
public:
    MotionPlanner(const CoordinateMapperMock& mapper, 
                  double safeHeightZ = 50.0, 
                  double pickHeightZ = 5.0);

    std::vector<Pose> planMove(const std::string& fromSquare, const std::string& toSquare) const;

private:
    CoordinateMapperMock mapper_;
    double safeHeightZ_;
    double pickHeightZ_;
    
    const Pose HOME_POSE = {0.0, 0.0, 150.0, GripperState::OPEN, "HOME"};
};

} // namespace ac

#endif // MOTION_PLANNER_HPP