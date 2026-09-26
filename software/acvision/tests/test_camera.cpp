/**
 * @file test_camera.cpp
 * @brief Hardware-dependent integration tests for the Camera abstraction.
 */

#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>

#include "camera/camera.hpp"

TEST(CameraTest, Initialization)
{
    EXPECT_NO_THROW({
        ac::Camera cam(0);
    });
}

TEST(CameraTest, FrameCapture)
{
    ac::Camera cam(0);

    cv::Mat frame;
    const bool success = cam.capture_frame(frame);

    EXPECT_TRUE(success) << "Failed to read a frame from the physical camera.";
    EXPECT_FALSE(frame.empty()) << "Camera read succeeded, but the OpenCV frame is empty.";
}
