#ifndef ACMOTION_MOTION_EXECUTION_HPP
#define ACMOTION_MOTION_EXECUTION_HPP

#include <chrono>
#include <cstdint>
#include <vector>

#include "motion/joint_trajectory.hpp"
#include "motion/motion_protocol.hpp"
#include "motion/motion_transport.hpp"

namespace ac::motion {

/**
 * @enum MotionExecutionState
 * @brief Synchronous host-side execution state exposed for diagnostics/FSM integration.
 */
enum class MotionExecutionState {
    Idle,
    Sending,
    WaitingAck,
    WaitingDone,
    Completed,
    Error,
    SafeStop,
    Cancelled
};

/**
 * @enum MotionExecutionResult
 * @brief Terminal result returned by one trajectory execution attempt.
 */
enum class MotionExecutionResult {
    Success,
    Timeout,
    ProtocolError,
    ControllerError,
    EmergencyStop,
    LimitTriggered,
    Cancelled
};

/**
 * @class MotionExecution
 * @brief Coordinates joint-segment delivery and controller acknowledgements.
 *
 * Runs on the Linux SBC. It serializes already-computed JointSegment values
 * through MotionProtocol and communicates using an abstract IMotionTransport.
 *
 * MotionExecution does not perform inverse kinematics, interpolation, motion
 * profiling, STEP/DIR generation, chess logic, or GPIO access.
 */
class MotionExecution {
public:
    /**
     * @brief Creates an execution coordinator.
     * @param transport Hardware-independent transport implementation.
     * @param ackTimeout Maximum wait for ACK after sending a segment.
     * @param doneTimeout Maximum wait for DONE after ACK.
     * @note transport must outlive this instance.
     */
    MotionExecution(
        IMotionTransport& transport,
        std::chrono::milliseconds ackTimeout = std::chrono::milliseconds{500},
        std::chrono::milliseconds doneTimeout = std::chrono::milliseconds{10000}
    );

    /**
     * @brief Executes all joint segments sequentially.
     * @param trajectory Ordered non-empty joint trajectory.
     * @return Structured terminal result.
     *
     * @throws std::invalid_argument when trajectory is empty, sequence IDs are
     *         zero/non-increasing, or timeout values are non-positive.
     *
     * @post state() is Completed on Success, SafeStop on safety events, or
     *       Error on timeout/protocol/controller failures.
     */
    [[nodiscard]] MotionExecutionResult execute(
        const std::vector<JointSegment>& trajectory
    );

    /**
     * @brief Sends an explicit cancellation request for the active sequence.
     * @return true when the cancel frame was accepted by the transport.
     *
     * @post state() becomes Cancelled when transmission succeeds.
     */
    bool cancel();

    /**
     * @brief Returns the current host-side execution state.
     */
    [[nodiscard]] MotionExecutionState state() const noexcept;

    /**
     * @brief Returns the most recently active command sequence.
     */
    [[nodiscard]] std::uint32_t activeSequence() const noexcept;

private:
    /**
     * @brief Waits for and validates one expected event for a sequence.
     * @param sequence Expected sequence identifier.
     * @param expected Required normal event type (Ack or Done).
     * @param timeout Receive timeout.
     * @return Terminal/continue result encoded as MotionExecutionResult.
     *
     * Success means the expected event was received. Safety/error events map
     * directly to their terminal results.
     */
    MotionExecutionResult waitForEvent(
        std::uint32_t sequence,
        ControllerEventType expected,
        std::chrono::milliseconds timeout
    );

    IMotionTransport& transport_;                    ///< Underlying line transport.
    std::chrono::milliseconds ackTimeout_;           ///< ACK timeout.
    std::chrono::milliseconds doneTimeout_;          ///< Completion timeout.
    MotionExecutionState state_{MotionExecutionState::Idle}; ///< Current state.
    std::uint32_t activeSequence_{0};                ///< Active/last sequence.
};

} // namespace ac::motion

#endif
