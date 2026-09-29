#ifndef ACMOTION_MOTION_PROTOCOL_HPP
#define ACMOTION_MOTION_PROTOCOL_HPP

#include <cstdint>
#include <optional>
#include <string>

#include "motion/joint_trajectory.hpp"

namespace ac::motion {

/**
 * @enum ControllerEventType
 * @brief Events emitted by the ESP32-S3 motion controller.
 */
enum class ControllerEventType {
    Ack,           ///< Command accepted and queued for execution.
    Done,          ///< Command completed successfully.
    Error,         ///< Controller rejected/failed the command.
    EmergencyStop, ///< Emergency stop became active.
    LimitTriggered ///< Limit/endstop interrupted execution.
};

/**
 * @struct ControllerEvent
 * @brief Parsed controller response associated with one command sequence.
 */
struct ControllerEvent {
    ControllerEventType type{ControllerEventType::Error}; ///< Event category.
    std::uint32_t sequence{0};                            ///< Command sequence.
    int errorCode{0};                                     ///< Controller error code for Error events.
};

/**
 * @class MotionProtocol
 * @brief Stateless codec for the versioned ACM1 SBC↔ESP32-S3 text protocol.
 *
 * Frames are line-delimited ASCII for MVP diagnostics and firmware simplicity.
 * Chess semantics never cross this boundary.
 *
 * @warning ACM1 currently serializes J1/J2/Z/gripper only. The selected Dejan
 *          SCARA requires J3 as well. See #160 before using ACM1 for autonomous
 *          powered execution on the physical arm.
 *
 * Command examples:
 * @code
 * ACM1|42|SEG|0.523599|0.733038|25.000000|100.000000|800
 * ACM1|42|CANCEL
 * @endcode
 *
 * Response examples:
 * @code
 * ACM1|42|ACK
 * ACM1|42|DONE
 * ACM1|42|ERR|7
 * ACM1|42|ESTOP
 * ACM1|42|LIMIT
 * @endcode
 */
class MotionProtocol {
public:
    /**
     * @brief Encodes one joint segment command.
     * @param segment Valid joint-space segment.
     * @return One line-delimited ACM1 command frame.
     * @throws std::invalid_argument when sequence/duration/target values are invalid.
     */
    [[nodiscard]] static std::string encodeSegment(const JointSegment& segment);

    /**
     * @brief Encodes cancellation of one command sequence.
     * @param sequence Non-zero sequence identifier.
     * @return One line-delimited ACM1 cancel frame.
     * @throws std::invalid_argument when sequence is zero.
     */
    [[nodiscard]] static std::string encodeCancel(std::uint32_t sequence);

    /**
     * @brief Parses one controller response line.
     * @param line Line without transport-specific framing requirements.
     * @return Parsed event, or std::nullopt for malformed/unsupported frames.
     */
    [[nodiscard]] static std::optional<ControllerEvent> parseEvent(
        const std::string& line
    );

private:
    /**
     * @brief Validates numeric and range invariants for one joint segment.
     * @param segment Segment to validate.
     * @throws std::invalid_argument when any invariant is violated.
     */
    static void validateSegment(const JointSegment& segment);
};

} // namespace ac::motion

#endif
