/**
 * @file camera.cpp
 * @brief Implementation of the ac::Camera class using the DirectShow backend.
 * @author Enzo R. L. D. Ribas - Atom Laboratory Founder and Lead Researcher
 * @version 1.0.0
 */

#include "camera/camera.hpp"
#include <opencv2/imgproc.hpp> //cv::cvtColor e cv::COLOR_BGR2GRAY;
#include <iostream>

namespace ac {

/**
 * @details Uses `cv::CAP_DSHOW` as the preferred backend on Windows. 
 * DirectShow provides faster initialization and more stable frame rates 
 * for USB 2.0/3.0 webcams compared to the Media Foundation (MSMF) backend.
 */
Camera::Camera(int device_id, int width, int height,  Backend backend) : m_id(device_id) {
    
    int api = 0; // Default to auto-detect

    switch (backend){
        case Backend::DSHOW:
            #ifdef _WIN32 
                api = cv::CAP_DSHOW;
            #endif
            break;
        case Backend::V4L2:
            #ifdef __linux__
                api = cv::CAP_V4L2;
            #endif
            break;
        default:
            api = 0;

        }

        m_cap.open(m_id, api);

    if (!m_cap.isOpened()) {
        std::cerr << "[ACVISION][CRITICAL]: Failed to claim Camera ID " 
        << m_id << ". Check if another app is using it." << std::endl;
    }else{
        // Set resolution if the camera was successfully opened
        m_cap.set(cv::CAP_PROP_FRAME_WIDTH, width);
        m_cap.set(cv::CAP_PROP_FRAME_HEIGHT, height);

        double actual_width = m_cap.get(cv::CAP_PROP_FRAME_WIDTH);
        double actual_height = m_cap.get(cv::CAP_PROP_FRAME_HEIGHT);

        std::cout << "[ACVISION][INFO] Camera " << m_id 
                  << " initialized at " << actual_width << "x" << actual_height << std::endl;
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

/**
 * @brief Localiza valores de intensidade mínima e máxima.
 * @details Converte o frame BGR para 1 canal (Grayscale) para evitar crash no cv::minMaxLoc.
 */
void Camera::get_min_max_intensity(double* min_val, double* max_val) {
    cv::Mat frame = capture_frame();
    
    if (frame.empty()) {
        if (min_val) *min_val = 0.0;
        if (max_val) *max_val = 0.0;
        return;
    }

    //  Fix está aqui:
    cv::Mat gray;
    cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY); // BGR (3 canais) -> Gray (1 canal)
    
    cv::minMaxLoc(gray, min_val, max_val);
}

bool Camera::is_opened() const {
    return m_cap.isOpened();
}

} // namespace ac