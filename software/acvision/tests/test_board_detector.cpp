/**
 * @file test_board_detector.cpp
 * @brief Unit tests for chessboard detection using deterministic 2D images.
 */
#include <gtest/gtest.h>

#include "board_vision/board_vision.hpp"

#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>

#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#ifndef TEST_IMAGES_DIR
#define TEST_IMAGES_DIR "."
#endif

namespace {

std::filesystem::path testImagesDir() {
    return std::filesystem::path(TEST_IMAGES_DIR);
}

cv::Mat createSyntheticChessboard() {
    constexpr int squaresPerSide = 8;
    constexpr int squareSize = 50;
    constexpr int margin = 40;
    constexpr int boardSize = squaresPerSide * squareSize;
    constexpr int imageSize = boardSize + 2 * margin;

    cv::Mat image(imageSize, imageSize, CV_8UC3, cv::Scalar(220, 220, 220));

    for (int row = 0; row < squaresPerSide; ++row) {
        for (int col = 0; col < squaresPerSide; ++col) {
            const bool darkSquare = ((row + col) % 2) == 0;
            const cv::Scalar color = darkSquare ? cv::Scalar(25, 25, 25)
                                                : cv::Scalar(245, 245, 245);

            cv::Rect square(
                margin + col * squareSize,
                margin + row * squareSize,
                squareSize,
                squareSize
            );
            cv::rectangle(image, square, color, cv::FILLED);
        }
    }

    return image;
}

cv::Mat createSyntheticImageWithoutBoard() {
    cv::Mat image(480, 640, CV_8UC3, cv::Scalar(180, 180, 180));

    cv::circle(image, cv::Point(150, 120), 40, cv::Scalar(80, 120, 200), cv::FILLED);
    cv::circle(image, cv::Point(420, 300), 65, cv::Scalar(200, 90, 70), cv::FILLED);
    cv::line(image, cv::Point(40, 420), cv::Point(580, 60), cv::Scalar(120, 120, 120), 3);

    return image;
}

bool writePngImage(const std::filesystem::path& path, const cv::Mat& image) {
    if (cv::imwrite(path.string(), image)) {
        return true;
    }

    std::vector<uchar> encoded;
    if (!cv::imencode(".png", image, encoded)) {
        return false;
    }

    std::ofstream output(path.string(), std::ios::out | std::ios::binary | std::ios::trunc);
    if (!output) {
        return false;
    }

    output.write(reinterpret_cast<const char*>(encoded.data()), static_cast<std::streamsize>(encoded.size()));
    return output.good();
}

cv::Mat loadOrCreateImage(const std::string& fileName, const cv::Mat& fallbackImage) {
    const auto path = testImagesDir() / fileName;

    if (!std::filesystem::exists(path)) {
        std::filesystem::create_directories(path.parent_path());
        const bool written = writePngImage(path, fallbackImage);
        EXPECT_TRUE(written) << "Failed to create test image: " << path;
    }

    cv::Mat image = cv::imread(path.string(), cv::IMREAD_COLOR);
    EXPECT_FALSE(image.empty()) << "Failed to load test image: " << path;

    return image;
}

void expectPointInsideImage(const cv::Point2f& point, const cv::Mat& image) {
    EXPECT_GE(point.x, 0.0f);
    EXPECT_GE(point.y, 0.0f);
    EXPECT_LT(point.x, static_cast<float>(image.cols));
    EXPECT_LT(point.y, static_cast<float>(image.rows));
}

} // namespace

TEST(BoardDetectorTest, DetectsChessboardImageAndReturnsFourCorners) {
    const cv::Mat fallbackImage = createSyntheticChessboard();
    ASSERT_FALSE(fallbackImage.empty());

    const cv::Mat image = loadOrCreateImage("chessboard.png", fallbackImage);
    ASSERT_FALSE(image.empty());

    ac::BoardDetector detector;
    const auto result = detector.detect(image);

    ASSERT_TRUE(result.has_value());
    ASSERT_EQ(result->corners.size(), 4U);

    for (const auto& corner : result->corners) {
        expectPointInsideImage(corner, image);
    }
}

TEST(BoardDetectorTest, ReturnsNulloptWhenImageHasNoBoard) {
    const cv::Mat fallbackImage = createSyntheticImageWithoutBoard();
    ASSERT_FALSE(fallbackImage.empty());

    const cv::Mat image = loadOrCreateImage("no_board.png", fallbackImage);
    ASSERT_FALSE(image.empty());

    ac::BoardDetector detector;
    const auto result = detector.detect(image);

    EXPECT_FALSE(result.has_value());
}
