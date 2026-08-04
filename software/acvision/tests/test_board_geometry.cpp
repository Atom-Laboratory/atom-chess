#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>
#include <string>
#include <optional>
#include "board_vision/board_vision.hpp"

// Teste focado no fluxo real que o Enzo implementou
TEST(BoardVisionTest, TestRealBoardDetectionAndGeometry) {
    // 1. Carrega a imagem real que o Enzo disponibilizou
    std::string imagePath = "software/acvision/tests/images/chessboard.png";
    cv::Mat srcImage = cv::imread(imagePath);
    
    // Garante que o arquivo de imagem foi aberto com sucesso
    ASSERT_FALSE(srcImage.empty()) << "Erro: Nao foi possivel carregar a imagem de teste em: " << imagePath;

    // 2. Instancia a classe do projeto seguindo o namespace 'ac'
    ac::BoardDetector detector;

    // 3. Executa a detecção completa (que internamente faz a homografia e valida a geometria)
    std::optional<ac::BoardCorners> detectedBoard = detector.detect(srcImage);

    // 4. Validações do GoogleTest baseadas no retorno do código do Enzo
    // O Enzo disse que a imagem real nao tem problemas para deteccao, entao o optional NAO pode ser nulo
    ASSERT_TRUE(detectedBoard.has_value()) << "O algoritmo falhou em detectar o tabuleiro na imagem real.";

    // Garante que os 4 cantos foram encontrados e populados no array
    EXPECT_EQ(detectedBoard->corners.size(), 4);

    // Valida se os pontos possuem coordenadas coerentes (maiores que zero)
    for (const auto& point : detectedBoard->corners) {
        EXPECT_GE(point.x, 0.0f);
        EXPECT_GE(point.y, 0.0f);
    }
}