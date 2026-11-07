#include <cmath>
#include <iomanip>
#include <iostream>
#include <locale>
#include <optional>
#include <stdexcept>
#include <string_view>
#include <vector>

#include "motion/inverse_kinematics.hpp"
#include "motion/motion_planner.hpp"

int main(int argc, char** argv)
{
    using namespace ac::motion;
    std::cout.imbue(std::locale::classic());
    std::cout << std::setprecision(17);
    if (argc > 2 || (argc == 2 && std::string_view(argv[1]) != "--unreachable")) {
        std::cerr << "usage: export_mujoco_trajectory [--unreachable]\n";
        return 2;
    }
    constexpr double dx = 112.83706, dy = -90.32926;
    const double offset = std::atan2(dy, dx);
    CoordinateMapper mapper("");
    try {
        MotionPlanner planner(mapper, 83.68, 13.68);
        PhysicalTask task{};
        task.type = PhysicalTaskType::MoveBoardPiece;
        task.physicalSource = Point2D{260, 0};
        task.physicalTarget = Point2D{argc == 2 ? 1000.0 : 260.0, 40};
        const auto poses = planner.planTask(task);
        ScaraGeometry geometry{};
        geometry.link1Mm = 220;
        geometry.link2Mm = std::hypot(dx, dy);
        geometry.limits = {-2, 2, -2 + offset, 4 + offset, -7, 7, -100, 200};
        geometry.preferredElbow = ElbowConfiguration::Down;
        InverseKinematics ik(geometry);
        std::vector<JointTarget> targets;
        for (const auto& pose : poses) {
            const auto target = ik.solve(pose);
            if (!target) throw std::runtime_error("unreachable or joint limit exceeded");
            targets.push_back(*target);
        }
        std::cout << R"({"schema":1,"operation_id":"p015-e2-e3","status":"planned",)"
                  << R"("profile":"atom-v6-position-only","frame":"mujoco_world",)"
                  << R"("joints":["joint_base_to_link1","joint_z_axis_arm1","joint_arm1_link_arm2_link","finger_1","finger_2"],)"
                  << R"("units":["rad","m","rad","m","m"],"initial":[0,0.12,0,0,0],"waypoints":[)";
        for (std::size_t i = 0; i < poses.size(); ++i) {
            if (i != 0) std::cout << ',';
            const auto& pose = poses[i];
            const auto& joint = targets[i];
            const double finger = -.021 * (1 - joint.gripperPercent / 100);
            std::cout << "{\"phase\":\"" << pose.label << "\",\"position\":["
                      << joint.joint1Rad << ',' << joint.zMm / 1000 << ','
                      << joint.joint2Rad - offset << ',' << finger << ',' << finger
                      << "],\"xyz\":[" << (pose.x + 40) / 1000 << ',' << pose.y / 1000
                      << ',' << (pose.z + 17) / 1000 << "]}";
        }
        std::cout << "]}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        std::cout << R"({"schema":1,"operation_id":"p015-e2-e3","status":"failed","error":"planning rejected"})" << '\n';
        return 1;
    }
}
