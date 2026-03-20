/**
 * @file camera.cpp
 * @brief Implementation of the ac::Camera class using the DirectShow backend.
 * @author Enzo R. L. D. Ribas - Atom Laboratory Founder and Lead Researcher
 * @version 1.0.0
 */

#include "camera/camera.hpp"
#include <iostream>

namespace ac {

/**
 * @details Uses `cv::CAP_DSHOW` as the preferred backend on Windows. 
 * DirectShow provides faster initialization and more stable frame rates 
 * for USB 2.0/3.0 webcams compared to the Media Foundation (MSMF) backend.
 */
Camera::Camera(int device_id) : m_id(device_id) {
    m_cap.open(m_id, cv::CAP_DSHOW);

    if (!m_cap.isOpened()) {
        std::cerr << "[ACVISION][CRITICAL]: Failed to claim Camera ID " 
        << m_id << ". Check if another app is using it." << std::endl;
    }
}

/**
 * @details The release() call is explicit here to ensure that the driver 
 * closes the stream before the rest of the object members are destroyed.
 */
Camera::~Camera() {
    if (m_cap.isOpened()) {
        m_cap.release(); // explicit release on destruction
    }
}

/**
 * @details This method wraps `m_cap.read()`. In OpenCV, this is a synchronized 
 * call to grab() and retrieve(). 
 * @warning Calling this in a tight loop without a `waitKey` or `sleep` 
 * may saturate a single CPU core.
 */
cv::Mat Camera::capture_frame() {
    cv::Mat frame;
    if (!m_cap.read(frame)) {
    std::cerr << "[ACVISION][WARNING]: Frame dropped from device " << m_id << std::endl;
}
return frame;
}

bool Camera::is_opened() const {
    return m_cap.isOpened();
}

} // namespace ac