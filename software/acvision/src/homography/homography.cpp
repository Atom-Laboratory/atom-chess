#include "homography/homography.hpp"

#include <opencv2/imgproc.hpp>


namespace ac {


cv::Mat Homography::compute(
    const std::array<cv::Point2f,4>& corners
) const
{

    std::vector<cv::Point2f> src = {
        corners[0], // TL
        corners[1], // TR
        corners[2], // BR
        corners[3]  // BL
    };


    constexpr float SIZE = 800;


    std::vector<cv::Point2f> dst = {
        {0,0},
        {SIZE,0},
        {SIZE,SIZE},
        {0,SIZE}
    };


    return cv::getPerspectiveTransform(
        src,
        dst
    );
}



cv::Mat Homography::warp(
    const cv::Mat& frame,
    const cv::Mat& H,
    int size
) const
{

    cv::Mat result;


    cv::warpPerspective(
        frame,
        result,
        H,
        cv::Size(size,size)
    );


    return result;
}
}