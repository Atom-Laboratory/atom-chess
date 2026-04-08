#pragma once

#include <opencv2/core.hpp>
#include <array>
#include <optional>

namespace ac {
/**
 * @brief Representa os quatro cantos externos estimados do tabuleiro.
 *
 * A ordem esperada dos pontos é:
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
