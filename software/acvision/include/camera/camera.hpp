/**
 * @file camera.hpp
 * @brief Public interface for camera hardware abstraction.
 * @author Enzo R. L. D. Ribas - Atom Laboratory Founder and Lead Researcher
 * @version 1.0.0
 */

#pragma once 

#include <opencv2/core.hpp>
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
         * @brief Captures the current frame and computes its global min/max pixel intensity.
         * @details Internally delegates to @ref compute_min_max_intensity so the same
         * conversion/validation logic used here can also be exercised directly in unit
         * tests with synthetic cv::Mat instances (no physical camera required).
         * @param min_val Output pointer for the minimum intensity found (may be nullptr).
         * @param max_val Output pointer for the maximum intensity found (may be nullptr).
         */
        void get_min_max_intensity(double* min_val, double* max_val);

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

/**
 * @brief Computes the global min/max pixel intensity of a single frame.
 *
 * @details `cv::minMaxLoc` requires a single-channel matrix. This helper accepts
 * frames with 1 (grayscale), 3 (BGR) or 4 (BGRA) channels, converting to grayscale
 * with `cv::cvtColor` only when needed before delegating to `cv::minMaxLoc`.
 *
 * - An empty frame sets both outputs to 0.0 instead of touching `cv::minMaxLoc`.
 * - An unsupported channel count (anything other than 1, 3 or 4) also sets both
 *   outputs to 0.0 and logs a warning, rather than crashing with an OpenCV assertion.
 *
 * This function is intentionally free-standing (not a member of Camera) so it can be
 * unit-tested directly with synthetic `cv::Mat` instances, without requiring camera
 * hardware to be present (see Issue #26 and #35).
 *
 * @param frame The frame to analyze. May be empty.
 * @param min_val Output pointer for the minimum intensity found (may be nullptr).
 * @param max_val Output pointer for the maximum intensity found (may be nullptr).
 */
void compute_min_max_intensity(const cv::Mat& frame, double* min_val, double* max_val);

} // namespace ac