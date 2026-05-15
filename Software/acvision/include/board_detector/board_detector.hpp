#pragma once

#include <opencv2/core.hpp>
#include <array>
#include <optional>
#include <vector>

namespace ac {
/**
 * @brief Represents the four estimated outer corners of the board.
 *
 * The expected order of points is:
 * 0 - top-left
 * 1 - top-right
 * 2 - bottom-right
 * 3 - bottom-left
 */
struct BoardCorners {
    std::array<cv::Point2f, 4> corners;
};

/**
 * @brief Responsible for detecting a chessboard in an image.
 */
class BoardDetector {
public:
    /**
     * @brief Detects the chessboard in a frame.
     *
     * @param frame Input image.
     * @return std::optional<BoardCorners> Detected corners or std::nullopt.
     */
    std::optional<BoardCorners> detect(const cv::Mat& frame) const;

private:
    std::optional<BoardCorners> detectByChessboardPattern(const cv::Mat& frame) const;
    std::optional<BoardCorners> detectByContours(const cv::Mat& frame) const;
    static std::array<cv::Point2f, 4> orderCorners(const std::vector<cv::Point>& quad);
};

}
