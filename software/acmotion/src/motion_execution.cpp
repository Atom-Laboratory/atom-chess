#include "motion/motion_execution.hpp"

#include <stdexcept>

namespace ac::motion {

/**
 * @brief Initializes synchronous host-side execution timeouts and transport.
 */
MotionExecution::MotionExecution(
    IMotionTransport& transport,
    std::chrono::milliseconds ackTimeout,
    std::chrono::milliseconds doneTimeout)
    : transport_(transport),
      ackTimeout_(ackTimeout),
      doneTimeout_(doneTimeout)
{
    if (ackTimeout_.count() <= 0 || doneTimeout_.count() <= 0) {
        throw std::invalid_argument("MotionExecution timeouts must be positive");
    }
}

/**
 * @brief Receives one controller line and maps it to the expected execution event.
 *
 * Wrong sequence IDs and unexpected ACK/DONE ordering are treated as protocol
 * failures. ESTOP/LIMIT transition the host into SafeStop.
 */
MotionExecutionResult MotionExecution::waitForEvent(
    std::uint32_t sequence,
    ControllerEventType expected,
    std::chrono::milliseconds timeout)
{
    const auto line = transport_.receiveLine(timeout);
    if (!line.has_value()) {
        state_ = MotionExecutionState::Error;
        return MotionExecutionResult::Timeout;
    }

    const auto event = MotionProtocol::parseEvent(*line);
    if (!event.has_value() || event->sequence != sequence) {
        state_ = MotionExecutionState::Error;
        return MotionExecutionResult::ProtocolError;
    }

    if (event->type == expected) {
        return MotionExecutionResult::Success;
    }

    switch (event->type) {
        case ControllerEventType::EmergencyStop:
            state_ = MotionExecutionState::SafeStop;
            return MotionExecutionResult::EmergencyStop;

        case ControllerEventType::LimitTriggered:
            state_ = MotionExecutionState::SafeStop;
            return MotionExecutionResult::LimitTriggered;

        case ControllerEventType::Error:
            state_ = MotionExecutionState::Error;
            return MotionExecutionResult::ControllerError;

        case ControllerEventType::Ack:
        case ControllerEventType::Done:
            state_ = MotionExecutionState::Error;
            return MotionExecutionResult::ProtocolError;
    }

    state_ = MotionExecutionState::Error;
    return MotionExecutionResult::ProtocolError;
}

/**
 * @brief Validates and executes a strictly ordered joint trajectory.
 *
 * Every segment is fully validated before its transport side effects, then
 * transmitted sequentially using ACK followed by DONE semantics.
 */
MotionExecutionResult MotionExecution::execute(
    const std::vector<JointSegment>& trajectory)
{
    if (trajectory.empty()) {
        throw std::invalid_argument("Motion trajectory must not be empty");
    }

    std::uint32_t previousSequence = 0;
    for (const JointSegment& segment : trajectory) {
        if (segment.sequence == 0 || segment.sequence <= previousSequence) {
            throw std::invalid_argument(
                "Motion segment sequences must be strictly increasing and non-zero"
            );
        }

        // encodeSegment validates all remaining segment invariants before any
        // transport side effect occurs for this segment.
        (void)MotionProtocol::encodeSegment(segment);
        previousSequence = segment.sequence;
    }

    state_ = MotionExecutionState::Sending;

    for (const JointSegment& segment : trajectory) {
        activeSequence_ = segment.sequence;
        const std::string command = MotionProtocol::encodeSegment(segment);

        state_ = MotionExecutionState::Sending;
        if (!transport_.sendLine(command)) {
            state_ = MotionExecutionState::Error;
            return MotionExecutionResult::TransportError;
        }

        state_ = MotionExecutionState::WaitingAck;
        MotionExecutionResult result = waitForEvent(
            segment.sequence,
            ControllerEventType::Ack,
            ackTimeout_
        );
        if (result != MotionExecutionResult::Success) {
            return result;
        }

        state_ = MotionExecutionState::WaitingDone;
        result = waitForEvent(
            segment.sequence,
            ControllerEventType::Done,
            doneTimeout_
        );
        if (result != MotionExecutionResult::Success) {
            return result;
        }
    }

    state_ = MotionExecutionState::Completed;
    return MotionExecutionResult::Success;
}

/**
 * @brief Requests cancellation of the active/last in-flight sequence.
 */
bool MotionExecution::cancel()
{
    if (activeSequence_ == 0
        || state_ == MotionExecutionState::Idle
        || state_ == MotionExecutionState::Completed
        || state_ == MotionExecutionState::SafeStop) {
        return false;
    }

    const bool sent = transport_.sendLine(
        MotionProtocol::encodeCancel(activeSequence_)
    );

    if (sent) {
        state_ = MotionExecutionState::Cancelled;
    } else {
        state_ = MotionExecutionState::Error;
    }

    return sent;
}

/**
 * @brief Returns current host-side state without side effects.
 */
MotionExecutionState MotionExecution::state() const noexcept
{
    return state_;
}

/**
 * @brief Returns the active or most recently attempted command sequence.
 */
std::uint32_t MotionExecution::activeSequence() const noexcept
{
    return activeSequence_;
}

} // namespace ac::motion
