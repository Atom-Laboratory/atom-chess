#pragma once

#include <opencv2/core.hpp>
#include <array>
#include <optional>

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

class BoardDetector {
public:
    std::optional<BoardCorners> detect(const cv::Mat& frame) const;
};

}
