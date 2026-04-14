/**
 * @file board_detector.cpp
 * @brief Chessboard detection and corner estimation for camera calibration.
 */    
#include "vision/board_detector.hpp"

#include <opencv2/calib3d.hpp>
#include <opencv2/imgproc.hpp>
#include <algorithm>
#include <cmath>
#include <vector>

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
    if (frame.empty()) {
        return std::nullopt;
    }

    if (auto result = detectByChessboardPattern(frame)) {
        return result;
    }

    return detectByContours(frame);
}

/**
 * @brief Detecta o tabuleiro de xadrez em um frame.
 *
 * @param frame Imagem de entrada.
 * @return std::optional<BoardCorners> Cantos detectados ou std::nullopt.
 */
std::optional<BoardCorners> BoardDetector::detectByChessboardPattern(const cv::Mat& frame) const {
    cv::Mat gray;
    if (frame.channels() == 3) {
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
    } else {
        gray = frame.clone();
    }

    cv::Mat processed;
    cv::equalizeHist(gray, processed);
    cv::GaussianBlur(processed, processed, cv::Size(5, 5), 0);

    cv::Size patternSize(7, 7);
    std::vector<cv::Point2f> innerCorners;

    bool found = false;

#if CV_VERSION_MAJOR >= 4
    found = cv::findChessboardCornersSB(processed, patternSize, innerCorners);
#endif

    if (!found) {
        found = cv::findChessboardCorners(
            processed,
            patternSize,
            innerCorners,
            cv::CALIB_CB_ADAPTIVE_THRESH | cv::CALIB_CB_NORMALIZE_IMAGE
        );
    }

    if (!found) {
        return std::nullopt;
    }

    cv::cornerSubPix(
        gray,
        innerCorners,
        cv::Size(11, 11),
        cv::Size(-1, -1),
        cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 30, 0.1)
    );

    cv::Point2f tl_in = innerCorners[0];
    cv::Point2f tr_in = innerCorners[6];
    cv::Point2f bl_in = innerCorners[42];
    cv::Point2f br_in = innerCorners[48];

    cv::Point2f vx = (tr_in - tl_in) / 6.0f;
    cv::Point2f vy = (bl_in - tl_in) / 6.0f;

    cv::Point2f tl = tl_in - 0.5f * vx - 0.5f * vy;
    cv::Point2f tr = tr_in + 0.5f * vx - 0.5f * vy;
    cv::Point2f br = br_in + 0.5f * vx + 0.5f * vy;
    cv::Point2f bl = bl_in - 0.5f * vx + 0.5f * vy;

    return BoardCorners{{tl, tr, br, bl}};
}

/**
 * @brief Contour-based fallback detection.
 *
 * Attempts to detect a large convex quadrilateral in the image, which is useful
 * when the internal chessboard pattern is occluded by pieces or when contrast is insufficient.
 */
std::optional<BoardCorners> BoardDetector::detectByContours(const cv::Mat& frame) const {
    cv::Mat gray;
    if (frame.channels() == 3) {
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
    } else {
        gray = frame.clone();
    }

    cv::Mat blurred;
    cv::GaussianBlur(gray, blurred, cv::Size(5, 5), 0);

    cv::Mat edges;
    cv::Canny(blurred, edges, 50, 150);

    std::vector<std::vector<cv::Point>> contours;
    cv::findContours(edges, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);

    double bestArea = 0.0;
    std::vector<cv::Point> bestQuad;

    for (const auto& contour : contours) {
        double area = cv::contourArea(contour);
        if (area < 5000.0) {
            continue;
        }

        std::vector<cv::Point> approx;
        cv::approxPolyDP(contour, approx, 0.02 * cv::arcLength(contour, true), true);

        if (approx.size() == 4 && cv::isContourConvex(approx)) {
            if (area > bestArea) {
                bestArea = area;
                bestQuad = approx;
            }
        }
    }

    if (bestQuad.empty()) {
        return std::nullopt;
    }

    return BoardCorners{orderCorners(bestQuad)};
}

/**
 * @brief Orders the 4 corners of the quadrilateral.
 *
 * Order:
 * 0 - top-left
 * 1 - top-right
 * 2 - bottom-right
 * 3 - bottom-left
 */
std::array<cv::Point2f, 4> BoardDetector::orderCorners(const std::vector<cv::Point>& quad) {
    std::array<cv::Point2f, 4> ordered{};
    std::vector<cv::Point2f> pts;
    pts.reserve(4);

    for (const auto& p : quad) {
        pts.emplace_back(static_cast<float>(p.x), static_cast<float>(p.y));
    }

    auto sumCmp = [](const cv::Point2f& a, const cv::Point2f& b) {
        return (a.x + a.y) < (b.x + b.y);
    };

    auto diffCmp = [](const cv::Point2f& a, const cv::Point2f& b) {
        return (a.y - a.x) < (b.y - b.x);
    };

    ordered[0] = *std::min_element(pts.begin(), pts.end(), sumCmp); 
    ordered[2] = *std::max_element(pts.begin(), pts.end(), sumCmp);  
    ordered[1] = *std::min_element(pts.begin(), pts.end(), diffCmp); 
    ordered[3] = *std::max_element(pts.begin(), pts.end(), diffCmp); 

    return ordered;
}

} 
