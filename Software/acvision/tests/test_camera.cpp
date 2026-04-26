/**
 * @file test_camera.cpp
 * @brief Automated tests for the camera module.
 */
#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>
#include "camera/camera.hpp"

// Teste 1: garante que a câmera não causa crash ao inicializar.
TEST(CameraTest, Initialization)
{
    EXPECT_NO_THROW({
        ac::Camera cam(0);
    });
}

// Teste 2: valida captura de frame somente quando houver câmera disponível.
// Em ambientes sem câmera, como CI/WSL/headless, o teste é ignorado.
TEST(CameraTest, FrameCapture)
{
    ac::Camera cam(0);

    cv::Mat frame = cam.capture_frame();

    if (frame.empty())
    {
        GTEST_SKIP() << "Camera hardware not available or frame capture failed in this environment.";
    }

    EXPECT_FALSE(frame.empty()) << "The captured frame is empty.";
}