/**
 * @file camera.cpp
 * @brief Implementation of the ac::Camera class using the DirectShow backend.
 * @author Enzo R. L. D. Ribas - Atom Laboratory Founder and Lead Researcher
 * @version 1.0.0
 */

#include "camera/camera.hpp"
#include <opencv2/imgproc.hpp>
#include <iostream>
#include <utility>
#include <variant>

namespace ac {

namespace
{
    std::pair<int, int> resolution_to_size(Resolution resolution)
{
    switch (resolution)
    {
        case Resolution::VGA:
            return {640, 480};

        case Resolution::HD:
            return {1280, 720};

        case Resolution::FULL_HD:
            return {1920, 1080};
    }

    return {1280, 720};
}
int select_backend(Backend backend)
{
#ifdef _WIN32

    switch (backend)
    {
        case Backend::DSHOW:
            return cv::CAP_DSHOW;

        case Backend::MSMF:
            return cv::CAP_MSMF;

        default:
            return cv::CAP_ANY;
    }

#else

    switch (backend)
    {
        case Backend::V4L2:
            return cv::CAP_V4L2;

        case Backend::FFMPEG:
            return cv::CAP_FFMPEG;

        case Backend::GSTREAMER:
            return cv::CAP_GSTREAMER;

        default:
            return cv::CAP_ANY;
    }

#endif
}

}

/**
 * @details Uses `cv::CAP_DSHOW` as the preferred backend on Windows. 
 * DirectShow provides faster initialization and more stable frame rates 
 * for USB 2.0/3.0 webcams compared to the Media Foundation (MSMF) backend.
 */
Camera::Camera(
    int device_id, 
    Resolution resolution,
    Backend backend) : m_source(device_id),
      m_backend(backend)
    {
    
    auto [w, h] = resolution_to_size(resolution);

    m_width = w;
    m_height = h;

    int api = select_backend(backend);

    if (!m_cap.open(device_id, api))
    {
        std::cerr << "[ACVISION][CRITICAL] Unable to open camera "
                  << device_id << std::endl;
        return;
    }

    m_cap.set(cv::CAP_PROP_FRAME_WIDTH, m_width);
    m_cap.set(cv::CAP_PROP_FRAME_HEIGHT, m_height);
}

Camera::Camera(
    int device_id,
    int width,
    int height,
    Backend backend)
    : m_source(device_id),
      m_backend(backend),
      m_width(width),
      m_height(height)
{
    int api = select_backend(backend);

    if (!m_cap.open(device_id, api))
    {
        std::cerr << "[ACVISION][CRITICAL] Unable to open camera "
                  << device_id << std::endl;
        return;
    }

    m_cap.set(cv::CAP_PROP_FRAME_WIDTH, width);
    m_cap.set(cv::CAP_PROP_FRAME_HEIGHT, height);
}

Camera::Camera(
    const std::string& url,
    Backend backend)
    : m_source(url),
      m_backend(backend)
{
    int api = select_backend(backend);

    if (!m_cap.open(url, api))
    {
        std::cerr << "[ACVISION][CRITICAL] Unable to open stream:\n"
                  << url << std::endl;
        return;
    }

    m_width = static_cast<int>(m_cap.get(cv::CAP_PROP_FRAME_WIDTH));
    m_height = static_cast<int>(m_cap.get(cv::CAP_PROP_FRAME_HEIGHT));
}

/**
 * @details The release() call is explicit here to ensure that the driver 
 * closes the stream before the rest of the object members are destroyed.
 */
Camera::~Camera() {
    if (m_cap.isOpened()) {
        m_cap.release();
    }
}

/**
 * @details This method wraps `m_cap.read()`. In OpenCV, this is a synchronized 
 * call to grab() and retrieve(). 
 * @warning Calling this in a tight loop without a `waitKey` or `sleep` 
 * may saturate a single CPU core.
 */
bool Camera::capture_frame(cv::Mat& frame){
    if (!m_cap.read(frame))
    {
        std::cerr << "[ACVISION][WARNING]: Frame dropped from device "
                  << std::get<int>(m_source) << std::endl;
        return false;
    }

    return true;
}

/**
 * @details Captures the current frame and forwards it to @ref compute_min_max_intensity,
 * which performs the channel handling and the actual `cv::minMaxLoc` call. Keeping that
 * logic in a free function (rather than inline here) is what allows it to be unit-tested
 * with synthetic frames instead of requiring real camera hardware.
 */
void Camera::get_min_max_intensity(double* min_val, double* max_val)
{
    cv::Mat frame;
    capture_frame(frame);
    compute_min_max_intensity(frame, min_val, max_val);
}

void compute_min_max_intensity(const cv::Mat& frame, double* min_val, double* max_val)
{
    if (frame.empty())
    {
        if (min_val) *min_val = 0.0;
        if (max_val) *max_val = 0.0;
        return;
    }

    // cv::minMaxLoc requires a single-channel matrix (Issue #26). Convert only when
    // the frame actually has more than one channel, instead of assuming BGR blindly.
    cv::Mat gray;
    const cv::Mat* target = &frame;

    switch (frame.channels())
    {
        case 1:
            // Already single-channel (e.g. grayscale source); no conversion needed.
            break;

        case 3:
            cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY); // BGR (3 canais) -> Gray (1 canal)
            target = &gray;
            break;

        case 4:
            cv::cvtColor(frame, gray, cv::COLOR_BGRA2GRAY); // BGRA (4 canais) -> Gray (1 canal)
            target = &gray;
            break;

        default:
            std::cerr << "[ACVISION][WARNING] compute_min_max_intensity: unsupported "
                          "channel count (" << frame.channels()
                      << "); returning 0 instead of calling cv::minMaxLoc." << std::endl;
            if (min_val) *min_val = 0.0;
            if (max_val) *max_val = 0.0;
            return;
    }

    cv::minMaxLoc(*target, min_val, max_val);
}

bool Camera::is_opened() const
{
    return m_cap.isOpened();
}

int Camera::width() const
{
    return static_cast<int>(m_cap.get(cv::CAP_PROP_FRAME_WIDTH));
}

int Camera::height() const
{
    return static_cast<int>(m_cap.get(cv::CAP_PROP_FRAME_HEIGHT));
}

double Camera::fps() const
{
    return m_cap.get(cv::CAP_PROP_FPS);
}

double Camera::actual_fps() const
{
    return m_cap.get(cv::CAP_PROP_FPS);
}

Camera::CameraInfo Camera::info() const
{
    return {
        width(),
        height(),
        fps(),
        m_backend
    };
}

} // namespace ac