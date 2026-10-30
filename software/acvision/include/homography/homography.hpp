#pragma once

#include <opencv2/core.hpp>
#include <array>


namespace ac {

class Homography {
public:

    cv::Mat compute(
        const std::array<cv::Point2f,4>& corners
    ) const;


    cv::Mat warp(
        const cv::Mat& frame,
        const cv::Mat& H,
        int size = 800
    ) const;

};

}