#ifndef ACMOTION_MOTION_TRANSPORT_HPP
#define ACMOTION_MOTION_TRANSPORT_HPP

#include <chrono>
#include <optional>
#include <string>
#include <string_view>

namespace ac::motion {

/**
 * @class IMotionTransport
 * @brief Hardware-independent line transport used by MotionExecution.
 *
 * Implementations may use UART, USB CDC, sockets, or a deterministic fake in
 * tests. This interface deliberately hides platform serial APIs from acmotion.
 */
class IMotionTransport {
public:
    virtual ~IMotionTransport() = default;

    /**
     * @brief Sends one complete protocol line.
     * @param line Encoded line including its trailing newline.
     * @return true when the transport accepted the bytes for transmission.
     */
    virtual bool sendLine(std::string_view line) = 0;

    /**
     * @brief Waits for one complete response line.
     * @param timeout Maximum blocking duration.
     * @return Response line, or std::nullopt on timeout/transport failure.
     *
     * Implementations that need to distinguish timeout from hard IO failure
     * should expose that distinction in their platform-specific diagnostics;
     * MotionExecution conservatively treats absence as Timeout.
     */
    virtual std::optional<std::string> receiveLine(
        std::chrono::milliseconds timeout
    ) = 0;
};

} // namespace ac::motion

#endif
