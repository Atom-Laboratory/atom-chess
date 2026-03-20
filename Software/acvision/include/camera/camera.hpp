/**
 * @file camera.hpp
 * @brief Persistent camera management for high-frequency frame acquisition.
 */

#pragma once
#include <opencv2/videoio.hpp>
#include <string>

namespace ac {

/**
 * @class CameraDevice
 * @brief Manages the lifecycle of a hardware camera stream.
 * * @details Uses a persistent VideoCapture instance to avoid the overhead of
 * re-initializing hardware on every frame request.
 */
class CameraDevice {
public:
    explicit CameraDevice(int device_id = 0);
    ~CameraDevice();

    // Disable copying to prevent multiple handles to the same hardware
    CameraDevice(const CameraDevice&) = delete;
    CameraDevice& operator=(const CameraDevice&) = delete;

    /**
     * @brief Fetches the next available frame from the buffer.
     * @return cv::Mat Captured frame. Check .empty() for validation.
     */
    cv::Mat get_frame();

    bool is_ready() const;

private:
    cv::VideoCapture m_cap;
    int m_id;
};

} // namespace ac