/**
 * @file capture_gui.cpp
 * @brief High-level GUI application for real-time camera monitoring.
 * @details Provides a continuous feedback loop with telemetry overlays.
 * @author Enzo R. L. D. Ribas - Atom Laboratory
 */

#include "camera/camera.hpp"
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>
#include <chrono>

int main() {
    const std::string window_name = "Atom Chess - Vision Monitor";
    cv::namedWindow(window_name, cv::WINDOW_AUTOSIZE);

    ac::Camera camera(0);

    std::cout << "[INFO] Starting Capture GUI. Press 'ESC' or 'Q' to exit." << std::endl;

    // Timing variables for FPS calculation
    auto last_time = std::chrono::high_resolution_clock::now();
    int frame_count = 0;
    float fps = 0;

    while (true) {
        // 1. Capture Logic
        cv::Mat frame = camera.capture_frame();

        if (frame.empty()) {
            std::cerr << "[ERROR] Lost connection to camera." << std::endl;
            break;
        }

        // 2. Telemetry Calculation (Performance Monitoring)
        frame_count++;
        auto current_time = std::chrono::high_resolution_clock::now();
        std::chrono::duration<float> elapsed = current_time - last_time;

        if (elapsed.count() >= 1.0f) {
            fps = frame_count / elapsed.count();
            frame_count = 0;
            last_time = current_time;
        }

        // 3. UI Overlay (Sits on top of the raw data)
        std::string info_text = "Res: " + std::to_string(frame.cols) + "x" + std::to_string(frame.rows) + 
                                " | FPS: " + std::to_string(static_cast<int>(fps));
        
        // Drawing a drop-shadow for better readability
        cv::putText(frame, info_text, cv::Point(11, 31), cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 0, 0), 2);
        cv::putText(frame, info_text, cv::Point(10, 30), cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 255, 0), 1);

        // 4. Rendering
        cv::imshow(window_name, frame);

        // 5. Event Handling (Input Polling)
        char key = static_cast<char>(cv::waitKey(1));
        if (key == 27 || key == 'q' || key == 'Q') { // 27 is ESC
            break;
        }
    }

    cv::destroyAllWindows();
    std::cout << "[INFO] GUI Session Terminated Cleanly." << std::endl;
    return 0;
}