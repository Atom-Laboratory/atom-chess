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
    
    cv::Mat frame;
    bool success = cam.capture_frame(frame);

    // 3. Asserções do GTest
    EXPECT_TRUE(success) << "Falha ao ler o frame da câmera de hardware.";
    EXPECT_FALSE(frame.empty()) << "O frame foi lido, mas a matriz do OpenCV está vazia (0 pixels).";
}

// -----------------------------------------------------------------------
// Testes de ac::compute_min_max_intensity (Issue #26 / Issue #35)
//
// A lógica de min/max foi extraída para uma função livre que recebe um
// cv::Mat, exatamente para permitir testá-la com matrizes sintéticas,
// sem depender de hardware de câmera real.
// -----------------------------------------------------------------------

// Teste 3: Frame vazio deve retornar min=0 e max=0, sem chamar cv::minMaxLoc.
TEST(MinMaxIntensityTest, EmptyFrameReturnsZero) {
    cv::Mat empty_frame;
    double min_val = -1.0;
    double max_val = -1.0;

    EXPECT_NO_THROW({
        ac::compute_min_max_intensity(empty_frame, &min_val, &max_val);
    });

    EXPECT_DOUBLE_EQ(min_val, 0.0);
    EXPECT_DOUBLE_EQ(max_val, 0.0);
}

// Teste 4: Frame de 1 canal (grayscale) não deve ser convertido e deve
// retornar os valores corretos de intensidade.
TEST(MinMaxIntensityTest, SingleChannelGrayReturnsCorrectValues) {
    cv::Mat gray(10, 10, CV_8UC1, cv::Scalar(50));
    gray.at<uchar>(2, 2) = 10;   // menor intensidade
    gray.at<uchar>(7, 7) = 220;  // maior intensidade

    double min_val = -1.0;
    double max_val = -1.0;

    ac::compute_min_max_intensity(gray, &min_val, &max_val);

    EXPECT_DOUBLE_EQ(min_val, 10.0);
    EXPECT_DOUBLE_EQ(max_val, 220.0);
}

// Teste 5 (Issue #26): Frame BGR de 3 canais não deve causar crash do
// cv::minMaxLoc (o bug original) e deve retornar valores coerentes após
// a conversão interna para escala de cinza.
TEST(MinMaxIntensityTest, ThreeChannelBGRDoesNotCrash) {
    cv::Mat bgr(10, 10, CV_8UC3, cv::Scalar(100, 100, 100));
    bgr.at<cv::Vec3b>(0, 0) = cv::Vec3b(0, 0, 0);
    bgr.at<cv::Vec3b>(9, 9) = cv::Vec3b(255, 255, 255);

    double min_val = -1.0;
    double max_val = -1.0;

    EXPECT_NO_THROW({
        ac::compute_min_max_intensity(bgr, &min_val, &max_val);
    });

    EXPECT_GE(min_val, 0.0);
    EXPECT_LE(max_val, 255.0);
    EXPECT_LT(min_val, max_val);
}

// Teste 6: Frame BGRA de 4 canais (ex.: capturas com canal alfa) também não
// deve causar crash, cobrindo o caso apontado na revisão do PR #34.
TEST(MinMaxIntensityTest, FourChannelBGRADoesNotCrash) {
    cv::Mat bgra(10, 10, CV_8UC4, cv::Scalar(80, 80, 80, 255));

    double min_val = -1.0;
    double max_val = -1.0;

    EXPECT_NO_THROW({
        ac::compute_min_max_intensity(bgra, &min_val, &max_val);
    });
}

// Teste 7: Ponteiros de saída nulos (uso defensivo da API) não devem causar crash.
TEST(MinMaxIntensityTest, NullOutputPointersDoNotCrash) {
    cv::Mat gray(5, 5, CV_8UC1, cv::Scalar(42));

    EXPECT_NO_THROW({
        ac::compute_min_max_intensity(gray, nullptr, nullptr);
    });
}