#pragma once

#include <opencv2/core.hpp>
#include <array>
#include <optional>

namespace ac {

struct BoardCorners {
    std::array<cv::Point2f, 4> corners;
};

class BoardDetector {
public:
    std::optional<BoardCorners> detect(const cv::Mat& frame) const;
};

}