#include <opencv2/opencv.hpp>
#include <chrono>
#include <iostream>
#include <vector>
#include <numeric>
#include <algorithm>

#include "board_detector/board_detector.hpp"

#ifndef TEST_IMAGES_DIR
#define TEST_IMAGES_DIR "../tests/images"
#endif

int main() {
    const std::string image_path = std::string(TEST_IMAGES_DIR) + "/chessboard.png";

    cv::Mat image = cv::imread(image_path);

    if (image.empty()) {
        std::cerr << "[ERROR] Could not load image: " << image_path << std::endl;
        return 1;
    }

    ac::BoardDetector detector;

    const int warmup_runs = 10;
    const int benchmark_runs = 1000;

    for (int i = 0; i < warmup_runs; ++i) {
        detector.detect(image);
    }

    std::vector<double> times_ms;
    times_ms.reserve(benchmark_runs);

    for (int i = 0; i < benchmark_runs; ++i) {
        auto start = std::chrono::high_resolution_clock::now();

        detector.detect(image);

        auto end = std::chrono::high_resolution_clock::now();

        double elapsed_ms =
            std::chrono::duration<double, std::milli>(end - start).count();

        times_ms.push_back(elapsed_ms);
    }

    double total_ms = std::accumulate(times_ms.begin(), times_ms.end(), 0.0);
    double avg_ms = total_ms / benchmark_runs;

    double min_ms = *std::min_element(times_ms.begin(), times_ms.end());
    double max_ms = *std::max_element(times_ms.begin(), times_ms.end());

    double fps = 1000.0 / avg_ms;

    std::cout << "\n========== BoardDetector Benchmark ==========\n";
    std::cout << "Image: " << image_path << "\n";
    std::cout << "Resolution: " << image.cols << "x" << image.rows << "\n";
    std::cout << "Warmup runs: " << warmup_runs << "\n";
    std::cout << "Benchmark runs: " << benchmark_runs << "\n";
    std::cout << "Average latency: " << avg_ms << " ms\n";
    std::cout << "Min latency: " << min_ms << " ms\n";
    std::cout << "Max latency: " << max_ms << " ms\n";
    std::cout << "Estimated FPS: " << fps << "\n";
    std::cout << "=============================================\n\n";

    return 0;
}