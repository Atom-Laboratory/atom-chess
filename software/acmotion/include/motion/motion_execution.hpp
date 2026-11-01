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
    Idle,       ///< No trajectory is currently being executed.
    Sending,    ///< Host is transmitting a command to the controller.
    WaitingAck, ///< Host waits for controller acceptance of the active segment.
    WaitingDone,///< Host waits for successful completion of the active segment.
    Completed,  ///< All trajectory segments completed successfully.
    Error,      ///< Execution stopped because of transport/protocol/controller failure.
    SafeStop,   ///< Execution stopped because of E-stop or a limit condition.
    Cancelled,  ///< Controller confirmed logical cancellation; not physical standstill.
    CancelRequested ///< CANCEL sent; waiting for matching CANCELLED.
};

/**
 * @enum MotionExecutionResult
 * @brief Terminal result returned by one trajectory execution attempt.
 */
enum class MotionExecutionResult {
    Success,        ///< Entire requested trajectory completed successfully.
    TransportError, ///< Host transport refused or failed command transmission.
    Timeout,        ///< Expected controller response was not received in time.
    ProtocolError,  ///< Malformed, unexpected or wrong-sequence response was received.
    ControllerError,///< ESP32-S3 explicitly reported an execution error.
    EmergencyStop,  ///< Emergency-stop event interrupted execution.
    LimitTriggered, ///< Limit/endstop event interrupted execution.
    Cancelled,      ///< Controller confirmed logical cancellation.
    RecoveryRequired ///< Latched state forbids starting another trajectory.
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
 * @note Single-owner, blocking API; not thread-safe or reentrant. Never call
 *       cancel(), execute(), diagnostics or transport concurrently. Live
 *       cancellation during execute() is not supported.
 *       shortcut: blocking execution; add the owner event loop in PR 4B.
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
     *         RecoveryRequired preserves a latched Error/SafeStop/Cancelled state.
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
     * @brief Requests and waits for logical cancellation after failed execution.
     * @return true only after matching CANCELLED, never merely on transmission.
     *
     * @pre execute() has returned Error with a possibly outstanding sequence.
     * @note Blocks for doneTimeout. DONE is not cancellation confirmation.
     *       No physical stop is proven. This does not clear a recovery latch.
     *       Idle/Completed/SafeStop/Cancelled calls return false without I/O.
     * @post Cancelled only on confirmation; failures remain Error or SafeStop.
     */
    bool cancel();

    /**
     * @brief Returns the current host-side execution state.
     * @return Current MotionExecutionState used by diagnostics/FSM integration.
     */
    [[nodiscard]] MotionExecutionState state() const noexcept;

    /**
     * @brief Returns the most recently active command sequence.
     * @return Last sequence sent or being processed; zero before any execution.
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
