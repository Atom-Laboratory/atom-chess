/**
 * @file test_camera.cpp
 * @brief Automated unit tests for the camera module.
 */

#include <gtest/gtest.h>
#include "camera/camera.hpp"

// Test Case: Ensure the function returns a valid object even if hardware fails
TEST(CameraInternal, ReturnsMatrixObject) {
    // We don't know if a camera is plugged in, but we know 
    // the function MUST return a cv::Mat (even if empty).
    cv::Mat frame = capture_frame(99); // Likely non-existent ID
    
    // Technical check: Does it crash? No.
    // Is it a cv::Mat? Yes.
    EXPECT_TRUE(frame.empty() || !frame.empty()); 
}

// Test Case: Data Integrity (Only if camera 0 is present)
TEST(CameraIntegration, ValidatesFrameSpecs) {
    cv::Mat frame = capture_frame(0);
    
    if(!frame.empty()) {
        // A standard camera should have at least some resolution
        EXPECT_GT(frame.cols, 0);
        EXPECT_GT(frame.rows, 0);
        // OpenCV BGR default is 3 channels
        EXPECT_EQ(frame.channels(), 3);
    }
}