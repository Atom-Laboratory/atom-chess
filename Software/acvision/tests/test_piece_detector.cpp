#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>
#include <array>

#include "piece_detector/piece_detector.hpp"

using namespace ac;

/**
 * @brief Testa se o detector processa as 64 células sem erro
 */
TEST(PieceDetectorTest, ProcessaTodasAsCelulas)
{
    PieceDetector detector;

    std::array<std::array<cv::Mat, 8>, 8> boardCells;

    // Inicializa todas como vazias
    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            boardCells[r][c] = cv::Mat::zeros(100, 100, CV_8UC3);
        }
    }

    auto result = detector.analyzeBoard(boardCells);

    // Verifica se todas foram classificadas como EMPTY
    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            EXPECT_EQ(result[r][c], CellState::EMPTY);
        }
    }
}

/**
 * @brief Testa detecção de peças branca e preta
 */
TEST(PieceDetectorTest, DetectaCores)
{
    PieceDetector detector;

    std::array<std::array<cv::Mat, 8>, 8> boardCells;

    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            boardCells[r][c] = cv::Mat::zeros(100, 100, CV_8UC3);
        }
    }

    // peça branca (círculo branco em fundo escuro)
    cv::Mat whiteCell = cv::Mat::zeros(100, 100, CV_8UC3);
    cv::circle(whiteCell, cv::Point(50,50), 20, cv::Scalar(255,255,255), -1);
    boardCells[0][0] = whiteCell;

    // peça preta (círculo escuro em fundo claro)
    cv::Mat blackCell = cv::Mat(100, 100, CV_8UC3, cv::Scalar(200,200,200));
    cv::circle(blackCell, cv::Point(50,50), 20, cv::Scalar(20,20,20), -1);
    boardCells[7][7] = blackCell;

    auto result = detector.analyzeBoard(boardCells);

    EXPECT_EQ(result[0][0], CellState::WHITE);
    EXPECT_EQ(result[7][7], CellState::BLACK);
}