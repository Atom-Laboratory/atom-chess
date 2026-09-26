/**
 * @file test_camera_min_max.cpp
 * @brief Deterministic unit tests for camera frame intensity helpers.
 */

#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>

#include "camera/camera.hpp"

TEST(MinMaxIntensityTest, EmptyFrameReturnsZero)
{
    cv::Mat empty_frame;
    double min_val = -1.0;
    double max_val = -1.0;

    EXPECT_NO_THROW(ac::compute_min_max_intensity(empty_frame, &min_val, &max_val));
    EXPECT_DOUBLE_EQ(min_val, 0.0);
    EXPECT_DOUBLE_EQ(max_val, 0.0);
}

TEST(MinMaxIntensityTest, SingleChannelGrayReturnsCorrectValues)
{
    cv::Mat gray(10, 10, CV_8UC1, cv::Scalar(50));
    gray.at<uchar>(2, 2) = 10;
    gray.at<uchar>(7, 7) = 220;

    double min_val = -1.0;
    double max_val = -1.0;

    ac::compute_min_max_intensity(gray, &min_val, &max_val);

    EXPECT_DOUBLE_EQ(min_val, 10.0);
    EXPECT_DOUBLE_EQ(max_val, 220.0);
}

TEST(MinMaxIntensityTest, ThreeChannelBGRDoesNotCrash)
{
    cv::Mat bgr(10, 10, CV_8UC3, cv::Scalar(100, 100, 100));
    bgr.at<cv::Vec3b>(0, 0) = cv::Vec3b(0, 0, 0);
    bgr.at<cv::Vec3b>(9, 9) = cv::Vec3b(255, 255, 255);

    double min_val = -1.0;
    double max_val = -1.0;

    EXPECT_NO_THROW(ac::compute_min_max_intensity(bgr, &min_val, &max_val));
    EXPECT_GE(min_val, 0.0);
    EXPECT_LE(max_val, 255.0);
    EXPECT_LT(min_val, max_val);
}

TEST(MinMaxIntensityTest, FourChannelBGRADoesNotCrash)
{
    cv::Mat bgra(10, 10, CV_8UC4, cv::Scalar(80, 80, 80, 255));
    double min_val = -1.0;
    double max_val = -1.0;

    EXPECT_NO_THROW(ac::compute_min_max_intensity(bgra, &min_val, &max_val));
}

TEST(MinMaxIntensityTest, NullOutputPointersDoNotCrash)
{
    cv::Mat gray(5, 5, CV_8UC1, cv::Scalar(42));
    EXPECT_NO_THROW(ac::compute_min_max_intensity(gray, nullptr, nullptr));
}
