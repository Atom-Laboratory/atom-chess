/**
 * @file board_detection_demo.cpp
 * @brief Application for demonstrating real-time chessboard detection.
 *
 * This executable captures frames from the camera and uses the BoardDetector module
 * to locate a chessboard in the image.
 *
 * When the board is found, the application draws:
 * - the four estimated corners of the board
 * - the lines of the corresponding quadrilateral
 * - a message indicating successful detection
 *
 * This application is intended for testing and visual validation of the initial
 * computer vision pipeline.
 */
#include "camera/camera.hpp"
#include "board_detector/board_detector.hpp"

#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>
#include <optional>

/**
 * @brief Main function for the board detection demo application.
 *
 * Initializes the camera, continuously captures frames, and attempts to detect
 * the chessboard in each captured frame.
 *
 * @return int Application exit code.
 */
int main() {
    ac::Camera cam(0, 640, 480, ac::Backend::V4L2);

    if (!cam.is_opened()) {
        std::cerr << "Erro ao abrir camera\n";
        return -1;
    }

    ac::BoardDetector detector;

    std::optional<ac::BoardCorners> lastResult;
    int frameCount = 0;

    while (true) {
        auto frame = cam.capture_frame();
        if (frame.empty()) {
            std::cerr << "Frame vazio.\n";
            break;
        }

        frameCount++;

        if (frameCount % 3 == 0) {
            cv::Mat smallFrame;
            cv::resize(frame, smallFrame, cv::Size(), 0.5, 0.5);

            auto detection = detector.detect(smallFrame);

            if (detection) {
                auto scaledCorners = detection->corners;

                for (auto& p : scaledCorners) {
                    p.x *= 2.0f;
                    p.y *= 2.0f;
                }

                lastResult = ac::BoardCorners{scaledCorners};
            } else {
                lastResult = std::nullopt;
            }
        }

        if (lastResult) {
            auto c = lastResult->corners;

            for (auto &p : c) {
                cv::circle(frame, p, 5, cv::Scalar(0, 0, 255), -1);
            }

            for (int i = 0; i < 4; i++) {
                cv::line(frame, c[i], c[(i + 1) % 4], cv::Scalar(255, 0, 0), 2);
            }

            cv::putText(frame, "Board detected", cv::Point(20, 30),
                        cv::FONT_HERSHEY_SIMPLEX, 0.8,
                        cv::Scalar(0, 255, 0), 2);
        } else {
            cv::putText(frame, "Board not detected", cv::Point(20, 30),
                        cv::FONT_HERSHEY_SIMPLEX, 0.8,
                        cv::Scalar(0, 0, 255), 2);
        }

        cv::imshow("Board", frame);

        int k = cv::waitKey(1);
        if (k == 27 || k == 'q' || k == 'Q') {
            break;
        }
    }

    return 0;
}
