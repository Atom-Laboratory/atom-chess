#include <opencv2/opencv.hpp>

#include <algorithm>
#include <chrono>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

#include "board_detector/board_detector.hpp"

int main(int argc, char** argv) {
    int camera_id = 0;

    if (argc > 1) {
        try {
            camera_id = std::stoi(argv[1]);
        } catch (...) {
            std::cerr << "[ERROR] Invalid camera id. Usage: ./benchmark_board_detector [camera_id]\n";
            return 1;
        }
    }

    cv::VideoCapture capture(camera_id);

    if (!capture.isOpened()) {
        std::cerr << "[ERROR] Could not open camera with id " << camera_id << ".\n";
        std::cerr << "[INFO] Make sure a webcam is connected and available as /dev/video"
                  << camera_id << ".\n";
        return 1;
    }

    capture.set(cv::CAP_PROP_FRAME_WIDTH, 640);
    capture.set(cv::CAP_PROP_FRAME_HEIGHT, 480);

    ac::BoardDetector detector;

    const int warmup_runs = 30;
    const int benchmark_runs = 300;

    cv::Mat frame;
    std::vector<double> times_ms;
    times_ms.reserve(benchmark_runs);

    std::cout << "\n========== BoardDetector Camera Benchmark ==========\n";
    std::cout << "Camera ID: " << camera_id << "\n";
    std::cout << "Warmup runs: " << warmup_runs << "\n";
    std::cout << "Benchmark runs: " << benchmark_runs << "\n";
    std::cout << "Requested resolution: 640x480\n";

    int valid_frames = 0;
    int dropped_frames = 0;

    for (int i = 0; i < warmup_runs; ++i) {
        capture >> frame;

        if (frame.empty()) {
            ++dropped_frames;
            continue;
        }

        detector.detect(frame);
    }

    for (int i = 0; i < benchmark_runs; ++i) {
        auto capture_start = std::chrono::high_resolution_clock::now();

        capture >> frame;

        if (frame.empty()) {
            ++dropped_frames;
            continue;
        }

        auto detection_start = std::chrono::high_resolution_clock::now();

        detector.detect(frame);

        auto detection_end = std::chrono::high_resolution_clock::now();

        double detection_ms =
            std::chrono::duration<double, std::milli>(detection_end - detection_start).count();

        times_ms.push_back(detection_ms);
        ++valid_frames;

        auto capture_end = std::chrono::high_resolution_clock::now();

        (void)capture_start;
        (void)capture_end;
    }

    if (times_ms.empty()) {
        std::cerr << "[ERROR] No valid frames were processed.\n";
        return 1;
    }

    double total_ms = std::accumulate(times_ms.begin(), times_ms.end(), 0.0);
    double avg_ms = total_ms / static_cast<double>(times_ms.size());

    double min_ms = *std::min_element(times_ms.begin(), times_ms.end());
    double max_ms = *std::max_element(times_ms.begin(), times_ms.end());

    double fps = 1000.0 / avg_ms;

    std::cout << "Actual frame resolution: " << frame.cols << "x" << frame.rows << "\n";
    std::cout << "Valid frames: " << valid_frames << "\n";
    std::cout << "Dropped frames: " << dropped_frames << "\n";
    std::cout << "Average detection latency: " << avg_ms << " ms\n";
    std::cout << "Min detection latency: " << min_ms << " ms\n";
    std::cout << "Max detection latency: " << max_ms << " ms\n";
    std::cout << "Estimated detection FPS: " << fps << "\n";
    std::cout << "====================================================\n\n";

    return 0;
}