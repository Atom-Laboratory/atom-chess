#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>
#include <array>

#include "piece_detector/piece_detector.hpp"

using namespace ac;

/**
 * @brief Verifies that the detector processes all 64 cells without errors.
 */
TEST(PieceDetectorTest, ProcessaTodasAsCelulas)
{
    PieceDetector detector;

    std::array<std::array<cv::Mat, 8>, 8> boardCells;

    // Initialize every cell as empty.
    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            boardCells[r][c] =
                cv::Mat::zeros(100, 100, CV_8UC3);
        }
    }

    BoardObservation result = detector.analyzeBoard(boardCells);

    // Verify that every cell is classified as EMPTY.
    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            EXPECT_EQ(result.cells[r][c], CellObservationState::EMPTY);
        }
    }
}

/**
 * @brief Verifies white and black piece color detection.
 */
TEST(PieceDetectorTest, DetectaCores)
{
    PieceDetector detector;

    std::array<std::array<cv::Mat, 8>, 8> boardCells;

    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            boardCells[r][c] =
                cv::Mat::zeros(100, 100, CV_8UC3);
        }
    }

    // White piece: white circle on a dark background.
    cv::Mat whiteCell =
        cv::Mat::zeros(100, 100, CV_8UC3);

    cv::circle(
        whiteCell,
        cv::Point(50, 50),
        20,
        cv::Scalar(255, 255, 255),
        -1
    );

    boardCells[0][0] = whiteCell;

    // Black piece: dark circle on a light background.
    cv::Mat blackCell(
        100,
        100,
        CV_8UC3,
        cv::Scalar(200, 200, 200)
    );

    cv::circle(
        blackCell,
        cv::Point(50, 50),
        20,
        cv::Scalar(20, 20, 20),
        -1
    );

    boardCells[7][7] = blackCell;

    BoardObservation result = detector.analyzeBoard(boardCells);

    EXPECT_EQ(result.cells[0][0], CellObservationState::WHITE);
    EXPECT_EQ(result.cells[7][7], CellObservationState::BLACK);
}
