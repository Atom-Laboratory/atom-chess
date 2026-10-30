/**
 * @file benchmark_piece_detector.cpp
 * @brief Dataset benchmark for the board-detection and PieceDetector pipeline.
 *
 * The benchmark evaluates the current vision contract only: EMPTY / WHITE /
 * BLACK observations for each of the 64 squares. Piece identity and legal chess
 * state belong to acchess and are intentionally outside this benchmark.
 */

#include <array>
#include <chrono>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include <opencv2/imgcodecs.hpp>

#include "board_observation/board_observation.hpp"
#include "board_vision/board_vision.hpp"
#include "homography/homography.hpp"
#include "piece_detector/piece_detector.hpp"

namespace fs = std::filesystem;

namespace {

using GroundTruthEntry = std::pair<std::string, std::string>;

std::vector<GroundTruthEntry> loadGroundTruth(const fs::path& filePath)
{
    std::vector<GroundTruthEntry> entries;
    std::ifstream file(filePath);
    std::string line;

    if (!file.is_open()) {
        std::cerr << "[ERROR] Cannot open ground truth file: " << filePath << '\n';
        return entries;
    }

    while (std::getline(file, line)) {
        std::stringstream stream(line);
        std::string imageName;
        std::string fen;

        if (!std::getline(stream, imageName, ',') || !std::getline(stream, fen)) {
            continue;
        }

        const auto first = fen.find_first_not_of(" \t");
        if (first == std::string::npos) {
            continue;
        }
        fen.erase(0, first);

        // Only the piece-placement field is required to derive EMPTY/WHITE/BLACK.
        const auto separator = fen.find(' ');
        entries.emplace_back(imageName, fen.substr(0, separator));
    }

    return entries;
}

bool parseObservationGroundTruth(
    const std::string& placement,
    ac::BoardObservation& expected)
{
    int row = 0;
    int col = 0;

    for (const char token : placement) {
        if (token == '/') {
            if (col != 8 || row >= 7) {
                return false;
            }
            ++row;
            col = 0;
            continue;
        }

        if (std::isdigit(static_cast<unsigned char>(token))) {
            const int emptyCount = token - '0';
            if (emptyCount < 1 || emptyCount > 8 || col + emptyCount > 8) {
                return false;
            }
            for (int i = 0; i < emptyCount; ++i) {
                expected.cells[row][col++] = ac::CellObservationState::EMPTY;
            }
            continue;
        }

        if (!std::isalpha(static_cast<unsigned char>(token)) || col >= 8) {
            return false;
        }

        expected.cells[row][col++] =
            std::isupper(static_cast<unsigned char>(token))
                ? ac::CellObservationState::WHITE
                : ac::CellObservationState::BLACK;
    }

    return row == 7 && col == 8;
}

std::array<std::array<cv::Mat, 8>, 8> splitBoard(const cv::Mat& topDown)
{
    std::array<std::array<cv::Mat, 8>, 8> cells{};
    const int cellWidth = topDown.cols / 8;
    const int cellHeight = topDown.rows / 8;

    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            const cv::Rect roi(
                col * cellWidth,
                row * cellHeight,
                cellWidth,
                cellHeight
            );
            cells[row][col] = topDown(roi);
        }
    }

    return cells;
}

bool isOccupied(ac::CellObservationState state)
{
    return state != ac::CellObservationState::EMPTY;
}

} // namespace

int main(int argc, char** argv)
{
#ifdef ACVISION_DATASET_DIR
    fs::path datasetPath = ACVISION_DATASET_DIR;
#else
    fs::path datasetPath = "software/acvision/tests/dataset";
#endif

    if (argc > 1) {
        datasetPath = argv[1];
    }

    if (!fs::exists(datasetPath) || !fs::is_directory(datasetPath)) {
        std::cerr << "[ERROR] Dataset directory not found: " << datasetPath << '\n';
        return 1;
    }

    const auto groundTruth = loadGroundTruth(datasetPath / "gabarito.txt");
    if (groundTruth.empty()) {
        std::cerr << "[ERROR] Ground truth is empty or invalid.\n";
        return 1;
    }

    ac::BoardDetector boardDetector;
    ac::Homography homography;
    ac::PieceDetector pieceDetector;

    std::size_t totalImages = 0;
    std::size_t imageLoadFailures = 0;
    std::size_t invalidGroundTruth = 0;
    std::size_t boardDetected = 0;
    std::size_t gridsExtracted = 0;

    std::size_t totalSquares = 0;
    std::size_t correctSquares = 0;

    std::size_t expectedOccupied = 0;
    std::size_t occupancyTruePositive = 0;
    std::size_t falsePositive = 0;
    std::size_t falseNegative = 0;
    std::size_t colorCorrect = 0;

    double totalProcessingMs = 0.0;

    for (const auto& [imageName, placement] : groundTruth) {
        ++totalImages;

        ac::BoardObservation expected{};
        if (!parseObservationGroundTruth(placement, expected)) {
            ++invalidGroundTruth;
            std::cerr << "[WARN] Invalid FEN placement for " << imageName << '\n';
            continue;
        }

        const cv::Mat image = cv::imread((datasetPath / imageName).string());
        if (image.empty()) {
            ++imageLoadFailures;
            std::cerr << "[WARN] Cannot read image: " << imageName << '\n';
            continue;
        }

        const auto started = std::chrono::steady_clock::now();

        const auto corners = boardDetector.detect(image);
        if (!corners) {
            const auto ended = std::chrono::steady_clock::now();
            totalProcessingMs +=
                std::chrono::duration<double, std::milli>(ended - started).count();
            std::cout << imageName << ": board-not-detected\n";
            continue;
        }
        ++boardDetected;

        const cv::Mat H = homography.compute(corners->corners);
        const cv::Mat topDown = homography.warp(image, H, 800);
        if (topDown.empty() || topDown.rows < 8 || topDown.cols < 8) {
            std::cout << imageName << ": invalid-warp\n";
            continue;
        }

        const auto cells = splitBoard(topDown);
        ++gridsExtracted;
        const ac::BoardObservation detected = pieceDetector.analyzeBoard(cells);

        const auto ended = std::chrono::steady_clock::now();
        totalProcessingMs +=
            std::chrono::duration<double, std::milli>(ended - started).count();

        std::size_t imageCorrect = 0;
        for (int row = 0; row < 8; ++row) {
            for (int col = 0; col < 8; ++col) {
                const auto exp = expected.cells[row][col];
                const auto got = detected.cells[row][col];

                ++totalSquares;
                if (exp == got) {
                    ++correctSquares;
                    ++imageCorrect;
                }

                const bool expOccupied = isOccupied(exp);
                const bool gotOccupied = isOccupied(got);

                if (expOccupied) {
                    ++expectedOccupied;
                }
                if (expOccupied && gotOccupied) {
                    ++occupancyTruePositive;
                    if (exp == got) {
                        ++colorCorrect;
                    }
                } else if (!expOccupied && gotOccupied) {
                    ++falsePositive;
                } else if (expOccupied && !gotOccupied) {
                    ++falseNegative;
                }
            }
        }

        std::cout << imageName << ": "
                  << imageCorrect << "/64 cells correct ("
                  << std::fixed << std::setprecision(1)
                  << (100.0 * static_cast<double>(imageCorrect) / 64.0)
                  << "%)\n";
    }

    const auto pct = [](std::size_t value, std::size_t total) {
        return total == 0
            ? 0.0
            : 100.0 * static_cast<double>(value) / static_cast<double>(total);
    };

    const std::size_t processedImages = gridsExtracted;

    std::cout << "\n========================================\n";
    std::cout << "PieceDetector benchmark summary\n";
    std::cout << "========================================\n";
    std::cout << "Dataset entries .............. " << totalImages << '\n';
    std::cout << "Image load failures .......... " << imageLoadFailures << '\n';
    std::cout << "Invalid ground truth ......... " << invalidGroundTruth << '\n';
    std::cout << "Board detection .............. " << boardDetected << "/" << totalImages
              << " (" << pct(boardDetected, totalImages) << "%)\n";
    std::cout << "Grid extraction .............. " << gridsExtracted << "/" << totalImages
              << " (" << pct(gridsExtracted, totalImages) << "%)\n";
    std::cout << "Cell classification accuracy . " << pct(correctSquares, totalSquares) << "%\n";
    std::cout << "Occupied-piece recall ........ " << pct(occupancyTruePositive, expectedOccupied) << "%\n";
    std::cout << "Color accuracy (detected) .... " << pct(colorCorrect, occupancyTruePositive) << "%\n";
    std::cout << "False positives .............. " << falsePositive << '\n';
    std::cout << "False negatives .............. " << falseNegative << '\n';
    std::cout << "Average processing time ...... "
              << (processedImages == 0 ? 0.0 : totalProcessingMs / processedImages)
              << " ms/image\n";
    std::cout << "========================================\n";

    // A benchmark run is valid even when accuracy is poor: the metrics are the
    // research output. Non-zero is reserved for fixture/input failures.
    return (imageLoadFailures == 0 && invalidGroundTruth == 0) ? 0 : 2;
}
