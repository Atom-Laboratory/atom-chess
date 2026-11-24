#include "motion/inverse_kinematics.hpp"
#include "motion/motion_planner.hpp"
#include <algorithm>
#include <cmath>
#include <string>
#include <stdexcept>

#ifdef _WIN32
#define API extern "C" __declspec(dllexport)
#else
#define API extern "C" __attribute__((visibility("default")))
#endif

namespace { thread_local std::string error; }
API const char* acmotion_error() { return error.c_str(); }
API int acmotion_version() { return 1; }

// XY/Z in world millimetres. Eight rows of X,Y,Z,gripper-percent.
API int acmotion_plan(const double* source, const double* target,
                      double safe_z, double pick_z, double* output)
{
    error.clear();
    try {
        if (!source || !target || !output) throw std::invalid_argument("NULL_PLAN_BUFFER");
        ac::motion::CoordinateMapper mapper("");
        ac::motion::MotionPlanner planner(mapper, safe_z, pick_z);
        ac::motion::PhysicalTask task{};
        task.type = ac::motion::PhysicalTaskType::MoveBoardPiece;
        task.physicalSource = ac::motion::Point2D{source[0], source[1]};
        task.physicalTarget = ac::motion::Point2D{target[0], target[1]};
        const auto poses = planner.planTask(task);
        if (poses.size() != 8) throw std::runtime_error("UNEXPECTED_PHASE_COUNT");
        for (size_t i = 0; i < poses.size(); ++i) {
            output[4*i] = poses[i].x;
            output[4*i+1] = poses[i].y;
            output[4*i+2] = poses[i].z;
            output[4*i+3] = poses[i].gripperPercent;
        }
        return 0;
    } catch (const std::exception& exception) { error = exception.what(); return -1; }
}

// Geometry vector is documented by the Python adapter. No project dimensions here.
API int acmotion_solve(const double* values, const double* world_pose,
                       int elbow_down, double* output)
{
    error.clear();
    try {
        if (!values || !world_pose || !output) throw std::invalid_argument("NULL_IK_BUFFER");
        for (int i = 0; i < 14; ++i)
            if (!std::isfinite(values[i])) throw std::invalid_argument("NONFINITE_GEOMETRY");
        using namespace ac::motion;
        ScaraGeometry geometry{};
        geometry.link1Mm = values[0];
        geometry.link2Mm = values[1];
        geometry.limits = {values[2], values[3], values[4], values[5],
                           -values[3]-values[5], -values[2]-values[4],
                           values[6], values[7]};
        geometry.preferredElbow = elbow_down ? ElbowConfiguration::Down : ElbowConfiguration::Up;
        Pose pose{};
        pose.x = world_pose[0]-values[9];
        pose.y = world_pose[1]-values[10];
        pose.z = world_pose[2]-values[11];
        pose.gripperPercent = world_pose[3];
        const auto solved = InverseKinematics(geometry).solve(pose);
        if (!solved) { error = "UNREACHABLE"; return -1; }
        output[0] = solved->joint1Rad;
        output[1] = solved->zMm/1000;
        output[2] = solved->joint2Rad-values[8];
        output[3] = values[12] + (values[13]-values[12])*pose.gripperPercent/100;
        output[4] = output[3];
        return 0;
    } catch (const std::exception& exception) { error = exception.what(); return -1; }
}
