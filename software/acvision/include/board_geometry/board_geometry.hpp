#ifndef BOARD_GEOMETRY_HPP
#define BOARD_GEOMETRY_HPP

#include <opencv2/opencv.hpp>
#include <vector>

// Task 1.3: Corrige a perspectiva usando Homografia (retorna imagem vista de cima)
cv::Mat corrigirPerspectiva(const cv::Mat& frameOriginal, const std::vector<cv::Point2f>& cantos);

// Task 1.4: Normaliza a imagem top-down para um tamanho quadrado fixo (ex: 800x800)
cv::Mat normalizarImagem(const cv::Mat& imagemTopDown, int tamanhoFixo = 800);

// Task 1.5: Divide a imagem normalizada em uma matriz 8x8 de casas (board[0][0] = topo esquerdo)
void segmentarTabuleiro(const cv::Mat& imagemNormalizada, cv::Mat board[8][8]);

#endif // BOARD_GEOMETRY_HPP