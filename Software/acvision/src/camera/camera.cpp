
/**
 * @file camera.cpp
 * @brief Logic for synchronous frame acquisition using OpenCv.
 * This Implementation focuses on RAII (Resource Acquisition Is Initialization)
 * for hardware resource management, ensuring that the camera device is properly released when the VideoCapture object goes out of scope. 
 * The function captures a single frame from the specified camera and returns it as a cv::Mat object. 
 * If the camera cannot be opened or the frame cannot be read, an empty cv::Mat will be returned.
 * @author Enzo R. L. D. Ribas - Atom Laboratory Founder and Lead Researcher
 */

#include "camera/camera.hpp"
#include <opencv2/videoio.hpp>
#include <iostream>

/**
 * @brief Captures a single synchronized frame from the specified hardware device.
 * 
 * @details On Windows, this function utilizes the `CAP_DSHOW` (DirectShow) backend.
 * DirectShow is preferred over MSMF for many USB webcams due to faster 
 * initialization and better support for legacy pixel formats.
 * 
 * @param camera_id The system index of the camera (starting at 0).
 * 
 * @return cv::Mat A container representing the captured image.
 * 
 * @retval cv::Mat::empty() returns true if the hardware failed to initialize 
 * or the frame buffer was corrupted/dropped.
 * 
 * @note **Memory Management:** `cv::Mat` acts as a smart pointer. The header 
 * (metadata) is copied, but the pixel data is reference-counted. 
 * Returning it by value is an O(1) operation.
 */
cv::Mat capture_frame(int camera_id) {
    // RAII: VideoCapture will automatically release the camera resource when it goes out of scope, preventing hardware deadlocks.
    cv::VideoCapture cap(camera_id, cv::CAP_DSHOW);

    if (!cap.isOpened()) {
        std::cerr << "[ACVISION] Error: Hardware failed to initialize for camera with ID "
                    << camera_id << " is in use or unavailable." << std::endl;
        return cv::Mat();
    }

    cv::Mat frame;

    /**
     * cap.read() is a wrapper for:
     * 1. cap.grab() - Grabs the next frame from the video file or camera and returns true (non-zero) in the case of success.
     * 2. cap.retrieve() - Retrieves the grabbed frame and stores it in the provided cv::Mat object.
    */
    bool success = cap.read(frame);

    if (!success) {
        std::cerr << "[ACVISION] Warning: Failed to read frame from camera with ID " << camera_id << std::endl;
        return cv::Mat();
    }

    return frame;
}