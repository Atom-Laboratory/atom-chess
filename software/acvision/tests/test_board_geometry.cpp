// #include <gtest/gtest.h>
// #include <string> // Correção explícita para o bug #25
// #include <vector>
// #include "board_geometry/board_geometry.hpp"

// // Teste para a Task 1.3: Homografia
// TEST(BoardGeometryTest, TestHomografiaEComputacaoDeMatriz) {
//     // Cria uma imagem preta de 1080p simulando o frame da câmera
//     cv::Mat frameOriginal(1080, 1920, CV_8UC3, cv::Scalar(0, 0, 0));
    
//     // Simula 4 cantos em perspectiva capturados no frame
//     std::vector<cv::Point2f> cantosFicticios = {
//         cv::Point2f(200, 150), cv::Point2f(800, 100),
//         cv::Point2f(850, 750), cv::Point2f(150, 700)
//     };

//     cv::Mat topDown = corrigirPerspectiva(frameOriginal, cantosFicticios);
    
//     // Verifica se a homografia gerou a imagem retificada no tamanho esperado (1000x1000)
//     EXPECT_FALSE(topDown.empty());
//     EXPECT_EQ(topDown.rows, 1000);
//     EXPECT_EQ(topDown.cols, 1000);
// }

// // Testes para as Tasks 1.4 e 1.5: Normalização e Segmentação
// TEST(BoardGeometryTest, TestNormalizacaoESegmentacao64Casas) {
//     // Cria uma imagem aérea genérica de 1000x1000
//     cv::Mat imagemTopDown(1000, 1000, CV_8UC3, cv::Scalar(0, 0, 0));
    
//     // Executa a Task 1.4: Normaliza para 800x800
//     cv::Mat imagemNormalizada = normalizarImagem(imagemTopDown, 800);
//     EXPECT_EQ(imagemNormalizada.rows, 800);
//     EXPECT_EQ(imagemNormalizada.cols, 800);
    
//     // Executa a Task 1.5: Segmenta em 8x8
//     cv::Mat board[8][8];
//     segmentarTabuleiro(imagemNormalizada, board);
    
//     // Garante que o canto superior esquerdo [0][0] e o inferior direito [7][7] têm 100x100 pixels
//     EXPECT_EQ(board[0][0].rows, 100);
//     EXPECT_EQ(board[0][0].cols, 100);
//     EXPECT_EQ(board[7][7].rows, 100);
//     EXPECT_EQ(board[7][7].cols, 100);
// }