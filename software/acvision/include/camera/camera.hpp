/**
 * @file camera.hpp
 * @brief Public interface for camera hardware abstraction.
 * @author Enzo R. L. D. Ribas - Atom Laboratory Founder and Lead Researcher
 * @version 1.0.0
 */

#pragma once 

#include <opencv2/videoio.hpp> 
#include <string>
#include <variant>

/**
 * @namespace ac
 * @brief Atom Chess root namespace for all vision and engine components.
 */
namespace ac {

    enum class Backend {
        AUTO,
        DSHOW,
        MSMF,
        V4L2,
        FFMPEG,
        GSTREAMER
    };

    enum class Resolution
    {
        VGA,
        HD,
        FULL_HD
    };

    /**
     * @class Camera
     * @brief High-level wrapper for OpenCV's VideoCapture with RAII semantics.
     * 
     * @details This class maintains a persistent connection to the camera hardware.
     * In contrast to stateless function calls, this object avoids the overhead of
     * re-initializing the camera for each frame capture.
     * 
     * @note This is **not thread-safe**. Concurrent calls to @code capture_frame() @endcode should be externally synchronized.
     * Otherwise will result in race conditions and undefined behavior.
     */
    class Camera {
    public:
        /**
         * @brief Constructor that initializes the hardware stream.
         * @param device_id The OS-level index of the camera (default: 0).
         * @warning This constructor does not throw on failure; it may log errors to stderr  
         *          if the device cannot be claimed. Use is_opened() to verify initialization.  

         */
        explicit Camera(
            int device_id, 
            Resolution resolution = Resolution::HD,
            Backend backend = Backend::AUTO
        );

        Camera(
            int device_id,
            int width,
            int height,
            Backend backend = Backend::AUTO
        );

        explicit Camera(
            const std::string& url,
            Backend backend = Backend::AUTO
        );

        /**
         * @brief Destructor. Ensures the hardware resource is released to the OS.
         * @see m_cap.release()
         */
        ~Camera();

        /**
         * @name Resource Management
         * @brief Deleted copy constructor and assignment operator to prevent accidental copying of the camera resource.
         * @details The camera resource is non-copyable because it represents a unique handle to the hardware. Copying would lead to multiple instances trying to manage the same resource, which can cause conflicts and undefined behavior.
         */
        ///@{
        Camera(const Camera&) = delete; // Disable copy constructor
        Camera& operator=(const Camera&) = delete; // Disable copy assignment
        ///@}

        /**
         * @brief Fetches the next available frame from the buffer.
         * @details This function blocks until a new frame is available. 
         * It returns an empty cv::Mat if the camera is not initialized or if there was an error during capture.
         * @return cv::Mat A container representing the captured image. 
         * The caller is responsible for checking if the returned cv::Mat is empty before using it.
         */
        bool capture_frame(cv::Mat& frame);

        /**
         * @brief Checks the current state of the hardware link.
         * @return true if the camera was successfully opened and is ready for I/O.
         */
        bool is_opened() const;

        int width() const;

        int height() const;

        double fps() const;
        double actual_fps() const;

        struct CameraInfo
        {
            int width;
            int height;
            double fps;
            Backend backend;
        };

        CameraInfo info() const;
    private:
        cv::VideoCapture m_cap; ///< The underlying OpenCV video capture handle.
        std::variant<int, std::string> m_source;
        Backend m_backend;
        int m_width;
        int m_height;
};

} // namespace ac