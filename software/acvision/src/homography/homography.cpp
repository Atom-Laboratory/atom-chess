#include "homography/homography.hpp"

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/calib3d.hpp>

namespace ac {

    /**
    * @brief Compute the Homography Transformation Matrix to a given set of corners.
    *
    * @param corners std::array<cv::Point2f,4> The set of 4 corners in tuple (x,y) of the 4 board corners.
    * @return The transformation matrix required to correct or change the perspective of an image
    */
    cv::Mat Homography::compute(
        const std::array<cv::Point2f,4>& corners
    ) const
    {

        cv::Point2f src[4] = {
            corners[0], // TL
            corners[1], // TR
            corners[2], // BR
            corners[3]  // BL
        };

        constexpr float SIZE = 800;

        cv::Point2f dst[4] = {
            cv::Point2f(0.0f, 0.0f),
            cv::Point2f(SIZE, 0.0f),
            cv::Point2f(SIZE, SIZE),
            cv::Point2f(0.0f, SIZE)
        };

        return cv::getPerspectiveTransform(src, dst);
    }

    /**
    * @brief Makes the warp transformation.
    *
    * @param frame cv::Mat The frame to be warped.
    * @param H The Transformation Matrix.
    */
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
            cv::Size(size, size)
        );

        return result;
    }
}