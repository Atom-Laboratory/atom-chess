/**
 * @file camera.hpp
 * @brief Public interface for camera hardware abstraction.
 * @author Enzo R. L. D. Ribas - Atom Laboratory Founder and Lead Researcher
 * @version 1.0.0
 */

#pragma once 

#include <opencv2/videoio.hpp> 
#include <opencv2/core.hpp> // FIX para cv::Mat, cv::Point;
#include <string>

/**
 * @namespace ac
 * @brief Atom Chess root namespace for all vision and engine components.
 */
namespace ac {

    enum class Backend {
        AUTO,
        DSHOW,
        V4L2
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
        explicit Camera(int device_id = 0, int width = 1280, int height = 720, Backend backend = Backend::AUTO);

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
         * @brief Localiza os valores de intensidade mínima e máxima no frame atual.
         * @details Converte o frame internamente para tons de cinza para evitar falhas de 
         * asserção do OpenCV com matrizes multi-canal (Issue #26).
         * * @param[out] min_val Ponteiro para armazenar o valor mínimo encontrado.
         * @param[out] max_val Ponteiro para armazenar o valor máximo encontrado.
         */
        void get_min_max_intensity(double* min_val, double* max_val);

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