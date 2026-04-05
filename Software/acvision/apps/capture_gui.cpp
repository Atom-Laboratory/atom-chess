#include "camera/camera.hpp"
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>
#include <chrono>

#include "fen_generator/fen_generator.hpp"

int main() {
    const std::string window_name = "Atom Chess - Vision Monitor";
    cv::namedWindow(window_name, cv::WINDOW_AUTOSIZE);

    ac::Camera camera(1, 1080, 720); 

    ac::FenGenerator fen_gen;

    if (!camera.is_opened()) return -1;

    std::cout << "[INFO] Starting Capture GUI. Press 'ESC' or 'Q' to exit." << std::endl;

    float smoothed_fps = 0.0f;
    const float alpha = 0.1f; 
    
    // Ponto de referência para medir o ciclo total (Frame-to-Frame)
    auto last_loop_end = std::chrono::high_resolution_clock::now();

    while (true) {
        // 1. Capture Logic
        cv::Mat frame = camera.capture_frame();

        if (frame.empty()) {
            std::cerr << "[ERROR] Lost connection to camera." << std::endl;
            break;
        }

        // 2. Telemetry Calculation (Real-world Loop Timing)
        auto current_loop_end = std::chrono::high_resolution_clock::now();
        std::chrono::duration<float, std::milli> frame_delta = current_loop_end - last_loop_end;
        last_loop_end = current_loop_end;

        // Instantaneous FPS Calculation
        float instant_fps = 1000.0f / frame_delta.count();

        // Exponential Moving Average for FPS
        if (smoothed_fps == 0) smoothed_fps = instant_fps;
        else smoothed_fps = (alpha * instant_fps) + (1.0f - alpha) * smoothed_fps;

        // 3. UI Overlay
        std::string latency_str = "Frame Delta: " + std::to_string(static_cast<int>(frame_delta.count())) + "ms";
        std::string fps_str = "EMA FPS: " + std::to_string(static_cast<int>(smoothed_fps));
        
        // Overlay (Drop Shadow + Text)
        cv::putText(frame, latency_str, cv::Point(11, 31), cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 0, 0), 2);
        cv::putText(frame, latency_str, cv::Point(10, 30), cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 255, 0), 1);
        cv::putText(frame, fps_str, cv::Point(11, 61), cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 0, 0), 2);
        cv::putText(frame, fps_str, cv::Point(10, 60), cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 255, 255), 1);

        // 4. Rendering
        cv::imshow(window_name, frame);

        // 5. Event Handling
        if (cv::waitKey(1) == 27 || cv::waitKey(1) == 113) break; 
    }

    cv::destroyAllWindows();
    return 0;
}