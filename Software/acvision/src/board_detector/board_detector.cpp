/**
 * @file board_detector.cpp
 * @brief Chessboard detection and corner estimation for camera calibration.
 */    
#include "vision/board_detector.hpp"

#include <opencv2/calib3d.hpp>
#include <opencv2/imgproc.hpp>

namespace ac {
/**
 * @brief Detects the chessboard in an image and estimates its four outer corners.
 *
 * The current algorithm:
 * 1. Converts the image to grayscale
 * 2. Detects the internal corners of the chessboard pattern (7x7)
 * 3. Refines the detected points with subpixel accuracy
 * 4. Extrapolates the four outer corners of the chessboard
 *
 * @param frame Input image in which to detect the chessboard.
 * @return std::optional<BoardCorners> Detected corners or std::nullopt.
 */
std::optional<BoardCorners> BoardDetector::detect(const cv::Mat& frame) const {
    if (frame.empty()) return std::nullopt;
    
    cv::Mat gray;
    cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);

    cv::Size pattern(7, 7);
    std::vector<cv::Point2f> corners;

    bool found = cv::findChessboardCorners(
        gray,
        pattern,
        corners,
        cv::CALIB_CB_ADAPTIVE_THRESH | cv::CALIB_CB_NORMALIZE_IMAGE
    );

    if (!found) return std::nullopt;

    cv::cornerSubPix(
        gray,
        corners,
        cv::Size(11,11),
        cv::Size(-1,-1),
        cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 30, 0.1)
    );

    cv::Point2f tl_in = corners[0];
    cv::Point2f tr_in = corners[6];
    cv::Point2f bl_in = corners[42];
    cv::Point2f br_in = corners[48];

    cv::Point2f vx = (tr_in - tl_in) / 6.0f;
    cv::Point2f vy = (bl_in - tl_in) / 6.0f;

    cv::Point2f tl = tl_in - 0.5f*vx - 0.5f*vy;
    cv::Point2f tr = tr_in + 0.5f*vx - 0.5f*vy;
    cv::Point2f br = br_in + 0.5f*vx + 0.5f*vy;
    cv::Point2f bl = bl_in - 0.5f*vx + 0.5f*vy;

    return BoardCorners{{tl, tr, br, bl}};
}

}
