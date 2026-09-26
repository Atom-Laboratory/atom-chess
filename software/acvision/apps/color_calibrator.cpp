/**
 * @file color_calibrator.cpp
 * @brief Interactive developer tool for persisting PieceDetector HSV profiles.
 *
 * This GUI tool is not part of the production headless runtime. It is intended
 * to be run during setup/calibration, then the generated YAML file is loaded
 * by PieceDetector on the Linux SBC.
 */

#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <string>

#include <opencv2/opencv.hpp>

#include "camera/camera.hpp"
#include "piece_detector/piece_detector_config.hpp"

namespace {

cv::Mat currentFrame;
cv::Point clickPoint;
bool clicked = false;

void onMouse(int event, int x, int y, int, void*)
{
    if (event == cv::EVENT_LBUTTONDOWN) {
        clickPoint = cv::Point(x, y);
        clicked = true;
    }
}

ac::ColorProfile calculateProfile(
    const cv::Mat& hsvImage,
    cv::Point point,
    int tolerance = 30)
{
    const cv::Vec3b hsv = hsvImage.at<cv::Vec3b>(point);
    const int h = hsv[0];
    const int s = hsv[1];
    const int v = hsv[2];

    ac::ColorProfile profile;
    profile.lowerBound = cv::Scalar(
        std::max(0, h - tolerance),
        std::max(0, s - tolerance),
        std::max(0, v - tolerance)
    );
    profile.upperBound = cv::Scalar(
        std::min(180, h + tolerance),
        std::min(255, s + tolerance),
        std::min(255, v + tolerance)
    );
    return profile;
}

} // namespace

int main(int argc, char** argv)
{
    const int deviceId = argc > 1 ? std::atoi(argv[1]) : 0;
    const std::string outputPath =
        argc > 2 ? argv[2] : "piece_detector_calibration.yml";

    ac::Camera camera(
        deviceId,
        ac::Resolution::VGA,
        ac::Backend::V4L2
    );

    if (!camera.is_opened()) {
        std::cerr << "[ERROR] Failed to open camera device " << deviceId << ".\n";
        return 1;
    }

    ac::PieceDetectorConfig config;
    config.useCalibration = true;

    cv::namedWindow("Calibration", cv::WINDOW_AUTOSIZE);
    cv::setMouseCallback("Calibration", onMouse);

    std::cout << "Piece color calibration\n"
              << "1. Place a WHITE piece in view and click on it.\n";

    bool whiteCalibrated = false;
    bool blackCalibrated = false;

    while (true) {
        if (!camera.capture_frame(currentFrame) || currentFrame.empty()) {
            std::cerr << "[ERROR] Failed to capture frame.\n";
            break;
        }

        cv::Mat displayFrame = currentFrame.clone();

        if (!whiteCalibrated) {
            cv::putText(
                displayFrame,
                "Click on a WHITE piece",
                cv::Point(10, 30),
                cv::FONT_HERSHEY_SIMPLEX,
                1.0,
                cv::Scalar(255, 255, 255),
                2
            );
        } else if (!blackCalibrated) {
            cv::putText(
                displayFrame,
                "Click on a BLACK piece",
                cv::Point(10, 30),
                cv::FONT_HERSHEY_SIMPLEX,
                1.0,
                cv::Scalar(0, 0, 0),
                2
            );
        } else {
            cv::putText(
                displayFrame,
                "Calibration complete - press ESC",
                cv::Point(10, 30),
                cv::FONT_HERSHEY_SIMPLEX,
                0.8,
                cv::Scalar(0, 255, 0),
                2
            );
        }

        cv::imshow("Calibration", displayFrame);

        if (clicked &&
            clickPoint.x >= 0 && clickPoint.x < currentFrame.cols &&
            clickPoint.y >= 0 && clickPoint.y < currentFrame.rows) {
            cv::Mat hsv;
            cv::cvtColor(currentFrame, hsv, cv::COLOR_BGR2HSV);

            if (!whiteCalibrated) {
                config.whiteProfile = calculateProfile(hsv, clickPoint);
                whiteCalibrated = true;
                std::cout << "White profile captured. Now click a BLACK piece.\n";
            } else if (!blackCalibrated) {
                config.blackProfile = calculateProfile(hsv, clickPoint);
                blackCalibrated = true;
                std::cout << "Black profile captured. Press ESC to save.\n";
            }

            clicked = false;
        }

        if (cv::waitKey(30) == 27) {
            break;
        }
    }

    cv::destroyAllWindows();

    if (!whiteCalibrated || !blackCalibrated) {
        std::cerr << "[ERROR] Calibration is incomplete; configuration was not saved.\n";
        return 2;
    }

    if (!config.save(outputPath)) {
        return 3;
    }

    std::cout << "Calibration saved to " << outputPath << "\n";
    return 0;
}
