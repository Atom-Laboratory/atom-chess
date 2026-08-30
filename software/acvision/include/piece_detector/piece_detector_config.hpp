#ifndef AC_PIECE_DETECTOR_CONFIG_HPP
#define AC_PIECE_DETECTOR_CONFIG_HPP

#include <opencv2/opencv.hpp>

namespace ac {

/**
 * @struct ColorProfile
 * @brief Stores color boundaries for detection using the HSV color space.
 */
struct ColorProfile {
    cv::Scalar lowerBound; /**< Lower color boundary (e.g., H_min, S_min, V_min) */
    cv::Scalar upperBound; /**< Upper color boundary (e.g., H_max, S_max, V_max) */
};

/**
 * @struct PieceDetectorConfig
 * @brief Injectable configuration for PieceDetector, containing calibration data.
 */
struct PieceDetectorConfig {
    bool useCalibration = false;
    ColorProfile whiteProfile;
    ColorProfile blackProfile;
};

}

#endif