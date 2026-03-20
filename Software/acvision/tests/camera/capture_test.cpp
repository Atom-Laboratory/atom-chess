#include "camera/camera.hpp"
#include <iostream>
#include <opencv2/highgui.hpp>

int main() {
    std::cout << "[TEST] Starting Camera Smoke Test..." << std::endl;

    // Act
    cv::Mat frame = capture_frame(0);

    // Assert (Technical Validation)
    if (frame.empty()) {
        std::cerr << "[FAIL] Frame is empty. Possible hardware or driver issue." << std::endl;
        return -1;
    }

    // Validate Metadata
    std::cout << "[SUCCESS] Frame captured successfully." << std::endl;
    std::cout << " > Resolution: " << frame.cols << "x" << frame.rows << std::endl;
    std::cout << " > Channels:   " << frame.channels() << " (Expected: 3 for BGR)" << std::endl;
    std::cout << " > Depth:      " << frame.depth() << " (Expected: 0 for CV_8U)" << std::endl;

    // Logic Validation: Check if the frame is not just a solid black/gray block
    double min, max;
    cv::minMaxLoc(frame, &min, &max);
    if (min == max) {
        std::cerr << "[WARNING] Static frame detected (all pixels have the same value)." << std::endl;
    } else {
        std::cout << "[PASS] Entropy check: Frame contains varied pixel data." << std::endl;
    }

    cv::imshow("Atom Chess - Vision Test", frame);
    cv::waitKey(0);

    return 0;
}