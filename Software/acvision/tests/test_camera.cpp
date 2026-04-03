/**
 * @file test_camera.cpp
 * @brief Automated unit tests for the camera module.
 */
#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>
#include "camera/camera.hpp"

// Teste 1: Garante que a câmera não "explode" ao inicializar
TEST(CameraTest, Initialization) {
    EXPECT_NO_THROW({
        ac::Camera cam(0); 
    });
}

// Teste 2: Garante que o frame capturado é válido e não está vazio
TEST(CameraTest, FrameCapture) {
    ac::Camera cam(0); // 1. Instancia o objeto
    

    cv::Mat frame = cam.capture_frame(); // 2. Captura um frame
    bool success = !frame.empty();

    // 3. Asserções do GTest
    EXPECT_TRUE(success) << "Falha ao ler o frame da câmera de hardware.";
    EXPECT_FALSE(frame.empty()) << "O frame foi lido, mas a matriz do OpenCV está vazia (0 pixels).";
}