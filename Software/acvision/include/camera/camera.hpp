/**
 * @file camera.hpp
 * @brief Public interface for camera hardware abstraction.
 * @author Enzo R. L. D. Ribas - Atom Laboratory Founder and Lead Researcher
 * @version 1.0.0
 */

#pragma once 

#include <opencv2/videoio.hpp> 
#include <string>

/**
 * @namespace ac
 * @brief Atom Chess root namespace for all vision and engine components.
 */
namespace ac {

    /**
     * @class Camera
     * @brief High-level wrapper for OpenCV's VideoCapture with RAII semantics.
     * 
     * @details This class maintains a persistent connection to the camera hardware.
     * In contrat to stateless function calls, this object avoids the overhead of
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
         * @throw May log errors to stderr if the device cannot be claimed.
         */
        explicit Camera(int device_id = 0);

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
        cv::Mat capture_frame();

        /**
         * @brief Checks the current state of the hardware link.
         * @return true if the camera was successfully opened and is ready for I/O.
         */
        bool is_opened() const;

    private:
        cv::VideoCapture m_cap; ///< The underlying OpenCV video capture handle.
        int m_id;   ///< Cached ID of the hardware device.
};

} // namespace ac