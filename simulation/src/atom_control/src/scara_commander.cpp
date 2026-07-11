#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "control_msgs/action/follow_joint_trajectory.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "std_msgs/msg/string.hpp"
#include "trajectory_msgs/msg/joint_trajectory_point.hpp"

using namespace std::chrono_literals;
using namespace std::placeholders;

class ScaraCommander : public rclcpp::Node
{
public:
  using FollowJointTrajectory = control_msgs::action::FollowJointTrajectory;
  using GoalHandle = rclcpp_action::ClientGoalHandle<FollowJointTrajectory>;

  ScaraCommander()
  : Node("scara_commander")
  {
    // TODO: ajustar para os nomes reais das juntas no URDF
    joint_names_ = {"shoulder_joint", "elbow_joint", "z_joint", "wrist_joint"};

    // TODO: ajustar para o nome real do controller no controller_manager
    action_client_ = rclcpp_action::create_client<FollowJointTrajectory>(
      this, "/scara_arm_controller/follow_joint_trajectory");

    startup_timer_ = create_wall_timer(
      500ms, std::bind(&ScaraCommander::send_test_goal, this));

    trigger_sub_ = create_subscription<std_msgs::msg::String>(
      "~/send_test_goal", 10,
      [this](const std_msgs::msg::String::SharedPtr) {send_test_goal();});
  }

private:
  void send_test_goal()
  {
    if (startup_timer_) {
      startup_timer_->cancel();
    }

    if (!action_client_->wait_for_action_server(5s)) {
      RCLCPP_ERROR(get_logger(), "Action server indisponivel apos 5s de espera");
      return;
    }

    trajectory_msgs::msg::JointTrajectoryPoint point;
    point.positions = {0.0, 0.0, 0.0, 0.0};  // TODO: pose "home" real
    point.time_from_start.sec = 2;
    point.time_from_start.nanosec = 0;

    FollowJointTrajectory::Goal goal;
    goal.trajectory.joint_names = joint_names_;
    goal.trajectory.points = {point};

    auto options = rclcpp_action::Client<FollowJointTrajectory>::SendGoalOptions();
    options.goal_response_callback = std::bind(&ScaraCommander::on_goal_response, this, _1);
    options.result_callback = std::bind(&ScaraCommander::on_result, this, _1);

    RCLCPP_INFO(get_logger(), "Enviando goal de teste");
    action_client_->async_send_goal(goal, options);
  }

  void on_goal_response(const GoalHandle::SharedPtr & goal_handle)
  {
    if (!goal_handle) {
      RCLCPP_ERROR(get_logger(), "Goal rejeitado pelo action server");
    } else {
      RCLCPP_INFO(get_logger(), "Goal aceito, executando");
    }
  }

  void on_result(const GoalHandle::WrappedResult & result)
  {
    switch (result.code) {
      case rclcpp_action::ResultCode::SUCCEEDED:
        RCLCPP_INFO(get_logger(), "Trajetoria concluida");
        break;
      case rclcpp_action::ResultCode::ABORTED:
        RCLCPP_ERROR(get_logger(), "Trajetoria abortada");
        break;
      case rclcpp_action::ResultCode::CANCELED:
        RCLCPP_WARN(get_logger(), "Trajetoria cancelada");
        break;
      default:
        RCLCPP_ERROR(get_logger(), "Codigo de resultado desconhecido");
        break;
    }
  }

  rclcpp_action::Client<FollowJointTrajectory>::SharedPtr action_client_;
  rclcpp::TimerBase::SharedPtr startup_timer_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr trigger_sub_;
  std::vector<std::string> joint_names_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ScaraCommander>());
  rclcpp::shutdown();
  return 0;
}