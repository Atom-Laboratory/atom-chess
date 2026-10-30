#pragma once

/**
 * @file robot_config.hpp
 * @brief Physical ESP32-S3 configuration for the Dejan SCARA adaptation.
 *
 * The repository intentionally ships with configured=false. Fill these values
 * from the physical-calibration record before enabling any motor motion.
 */
namespace atom_motion_config {

inline constexpr bool configured = false;

inline constexpr int j1StepPin = -1;
inline constexpr int j1DirPin = -1;
inline constexpr int j2StepPin = -1;
inline constexpr int j2DirPin = -1;
inline constexpr int j3StepPin = -1;
inline constexpr int j3DirPin = -1;
inline constexpr int zStepPin = -1;
inline constexpr int zDirPin = -1;

inline constexpr int j1LimitPin = -1;
inline constexpr int j2LimitPin = -1;
inline constexpr int j3LimitPin = -1;
inline constexpr int zLimitPin = -1;
inline constexpr int emergencyStopPin = -1;
inline constexpr int gripperServoPin = -1;

inline constexpr double j1StepsPerRad = 0.0;
inline constexpr double j2StepsPerRad = 0.0;
inline constexpr double j3StepsPerRad = 0.0;
inline constexpr double zStepsPerMm = 0.0;

inline constexpr bool j1InvertDirection = false;
inline constexpr bool j2InvertDirection = false;
inline constexpr bool j3InvertDirection = false;
inline constexpr bool zInvertDirection = false;

inline constexpr double maxStepperSpeed = 800.0;
inline constexpr double stepperAcceleration = 300.0;

inline constexpr int servoMinUs = 700;
inline constexpr int servoMaxUs = 2300;

inline constexpr bool limitsActiveLow = true;
inline constexpr bool emergencyStopActiveLow = true;

} // namespace atom_motion_config
