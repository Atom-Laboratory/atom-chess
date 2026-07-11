#include "homography/homography.hpp"

#include <opencv2/imgproc.hpp>


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
            cv::Size(size,size)
        );


        return result;
    }
}