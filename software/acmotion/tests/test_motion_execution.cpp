#include <gtest/gtest.h>

#include <chrono>
#include <deque>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "motion/motion_execution.hpp"

namespace ac::motion {
namespace {

class FakeMotionTransport final : public IMotionTransport {
public:
    bool sendLine(std::string_view line) override
    {
        sent.emplace_back(line);
        return sendSucceeds;
    }

    std::optional<std::string> receiveLine(
        std::chrono::milliseconds) override
    {
        if (onReceive) {
            onReceive();
        }
        if (responses.empty()) {
            return std::nullopt;
        }

        std::string response = responses.front();
        responses.pop_front();
        return response;
    }

    bool sendSucceeds{true};
    std::vector<std::string> sent;
    std::deque<std::string> responses;
    std::function<void()> onReceive;
};

JointSegment segment(std::uint32_t sequence)
{
    return JointSegment{
        sequence,
        {0.1, 0.2, -0.3, 25.0, 100.0},
        500
    };
}

TEST(MotionExecutionTest, ExecutesSegmentsSequentially)
{
    FakeMotionTransport transport;
    transport.responses = {
        "ACM1|1|ACK",
        "ACM1|1|DONE",
        "ACM1|2|ACK",
        "ACM1|2|DONE"
    };

    MotionExecution execution(transport);

    const auto result = execution.execute({
        segment(1),
        segment(2)
    });

    EXPECT_EQ(result, MotionExecutionResult::Success);
    EXPECT_EQ(execution.state(), MotionExecutionState::Completed);
    EXPECT_EQ(execution.activeSequence(), 2u);
    ASSERT_EQ(transport.sent.size(), 2u);
}

TEST(MotionExecutionTest, TimesOutWhenControllerDoesNotRespond)
{
    FakeMotionTransport transport;
    MotionExecution execution(
        transport,
        std::chrono::milliseconds{1},
        std::chrono::milliseconds{1}
    );

    const auto result = execution.execute({segment(1)});

    EXPECT_EQ(result, MotionExecutionResult::Timeout);
    EXPECT_EQ(execution.state(), MotionExecutionState::Error);
}

TEST(MotionExecutionTest, ReportsTransportFailure)
{
    FakeMotionTransport transport;
    transport.sendSucceeds = false;

    MotionExecution execution(transport);
    const auto result = execution.execute({segment(1)});

    EXPECT_EQ(result, MotionExecutionResult::TransportError);
    EXPECT_EQ(execution.state(), MotionExecutionState::Error);
}

TEST(MotionExecutionTest, EntersSafeStopOnEmergencyStop)
{
    FakeMotionTransport transport;
    transport.responses = {
        "ACM1|1|ESTOP"
    };

    MotionExecution execution(transport);
    const auto result = execution.execute({segment(1)});

    EXPECT_EQ(result, MotionExecutionResult::EmergencyStop);
    EXPECT_EQ(execution.state(), MotionExecutionState::SafeStop);
}

TEST(MotionExecutionTest, EntersSafeStopOnLimitSwitch)
{
    FakeMotionTransport transport;
    transport.responses = {
        "ACM1|1|ACK",
        "ACM1|1|LIMIT"
    };

    MotionExecution execution(transport);
    const auto result = execution.execute({segment(1)});

    EXPECT_EQ(result, MotionExecutionResult::LimitTriggered);
    EXPECT_EQ(execution.state(), MotionExecutionState::SafeStop);
}

TEST(MotionExecutionTest, RejectsWrongSequenceResponse)
{
    FakeMotionTransport transport;
    transport.responses = {
        "ACM1|99|ACK"
    };

    MotionExecution execution(transport);
    const auto result = execution.execute({segment(1)});

    EXPECT_EQ(result, MotionExecutionResult::ProtocolError);
    EXPECT_EQ(execution.state(), MotionExecutionState::Error);
}

TEST(MotionExecutionTest, PropagatesControllerError)
{
    FakeMotionTransport transport;
    transport.responses = {
        "ACM1|1|ACK",
        "ACM1|1|ERR|23"
    };

    MotionExecution execution(transport);
    const auto result = execution.execute({segment(1)});

    EXPECT_EQ(result, MotionExecutionResult::ControllerError);
    EXPECT_EQ(execution.state(), MotionExecutionState::Error);
}

TEST(MotionExecutionTest, CancelWithoutConfirmationDoesNotReportCancelled)
{
    FakeMotionTransport transport;
    MotionExecution execution(
        transport,
        std::chrono::milliseconds{1},
        std::chrono::milliseconds{1}
    );

    EXPECT_EQ(
        execution.execute({segment(7)}),
        MotionExecutionResult::Timeout
    );

    EXPECT_FALSE(execution.cancel());
    EXPECT_EQ(execution.state(), MotionExecutionState::Error);
    ASSERT_GE(transport.sent.size(), 2u);
    EXPECT_EQ(transport.sent.back(), "ACM1|7|CANCEL\n");
}

TEST(MotionExecutionTest, SafetyEventsOverrideUnexpectedSequencesAndLatch)
{
    for (const auto* event : {"ESTOP", "LIMIT"}) {
        FakeMotionTransport transport;
        transport.responses = {std::string{"ACM1|99|"} + event};
        MotionExecution execution(transport);
        EXPECT_EQ(execution.execute({segment(1)}), std::string{event} == "ESTOP"
            ? MotionExecutionResult::EmergencyStop : MotionExecutionResult::LimitTriggered);
        EXPECT_EQ(execution.state(), MotionExecutionState::SafeStop);
        transport.responses = {"ACM1|2|ACK", "ACM1|2|DONE"};
        EXPECT_NE(execution.execute({segment(2)}), MotionExecutionResult::Success);
        EXPECT_EQ(execution.state(), MotionExecutionState::SafeStop);
        EXPECT_EQ(transport.sent.size(), 1u);
    }
}

TEST(MotionExecutionTest, CancelRequiresMatchingTerminalConfirmation)
{
    FakeMotionTransport transport;
    MotionExecution execution(transport);
    EXPECT_EQ(execution.execute({segment(7), segment(8)}), MotionExecutionResult::Timeout);
    transport.responses = {"ACM1|7|CANCELLED"};
    transport.onReceive = [&execution] {
        EXPECT_EQ(execution.state(), MotionExecutionState::CancelRequested);
    };
    EXPECT_TRUE(execution.cancel());
    EXPECT_EQ(execution.state(), MotionExecutionState::Cancelled);
    EXPECT_TRUE(transport.responses.empty());
    ASSERT_EQ(transport.sent.size(), 2u);
    EXPECT_EQ(transport.sent.back(), "ACM1|7|CANCEL\n");
    EXPECT_EQ(execution.execute({segment(8)}), MotionExecutionResult::RecoveryRequired);
    EXPECT_EQ(transport.sent.size(), 2u);
    EXPECT_FALSE(execution.cancel());
}

TEST(MotionExecutionTest, FailedCancellationNeverConfirmsOrUnlocksExecution)
{
    for (const auto* response : {"ACM1|7|DONE", "ACM1|8|CANCELLED", "ACM1|7|ACK",
                                 "ACM1|7|ERR|105", "ACM1|7|CANCELLED|extra", "garbage", ""}) {
        SCOPED_TRACE(response);
        FakeMotionTransport transport;
        MotionExecution execution(transport);
        EXPECT_EQ(execution.execute({segment(7)}), MotionExecutionResult::Timeout);
        if (*response != '\0') {
            transport.responses = {response};
        }
        EXPECT_FALSE(execution.cancel());
        EXPECT_EQ(execution.state(), MotionExecutionState::Error);
        EXPECT_EQ(execution.execute({segment(8)}), MotionExecutionResult::RecoveryRequired);
        EXPECT_EQ(transport.sent.size(), 2u);
    }
}

TEST(MotionExecutionTest, CancelTransportFailureDoesNotWaitOrConfirm)
{
    FakeMotionTransport transport;
    MotionExecution execution(transport);
    EXPECT_EQ(execution.execute({segment(7)}), MotionExecutionResult::Timeout);
    transport.sendSucceeds = false;
    transport.responses = {"ACM1|7|CANCELLED"};
    EXPECT_FALSE(execution.cancel());
    EXPECT_EQ(execution.state(), MotionExecutionState::Error);
    EXPECT_EQ(transport.responses.size(), 1u);
    EXPECT_EQ(execution.execute({segment(8)}), MotionExecutionResult::RecoveryRequired);
}

TEST(MotionExecutionTest, CancellationSafetyEventsLatchRegardlessOfSequence)
{
    for (const auto* response : {"ACM1|7|ESTOP", "ACM1|99|ESTOP", "ACM1|7|LIMIT", "ACM1|99|LIMIT"}) {
        SCOPED_TRACE(response);
        FakeMotionTransport transport;
        MotionExecution execution(transport);
        EXPECT_EQ(execution.execute({segment(7)}), MotionExecutionResult::Timeout);
        transport.responses = {response};
        EXPECT_FALSE(execution.cancel());
        EXPECT_EQ(execution.state(), MotionExecutionState::SafeStop);
        EXPECT_FALSE(execution.cancel());
        EXPECT_EQ(execution.execute({segment(8)}), MotionExecutionResult::RecoveryRequired);
        EXPECT_EQ(transport.sent.size(), 2u);
    }
}

TEST(MotionExecutionTest, CancelWithoutOutstandingOperationDoesNotSend)
{
    FakeMotionTransport transport;
    MotionExecution execution(transport);
    EXPECT_FALSE(execution.cancel());
    EXPECT_TRUE(transport.sent.empty());
    transport.responses = {"ACM1|1|ACK", "ACM1|1|DONE"};
    EXPECT_EQ(execution.execute({segment(1)}), MotionExecutionResult::Success);
    EXPECT_FALSE(execution.cancel());
    EXPECT_EQ(execution.state(), MotionExecutionState::Completed);
    EXPECT_EQ(transport.sent.size(), 1u);
}

TEST(MotionExecutionTest, ProtocolAndControllerFailuresLatchBeforeNextTrajectory)
{
    for (const auto* response : {"garbage", "ACM1|1|ERR|7", "ACM1|1|CANCELLED", "ACM1|1|DONE"}) {
        SCOPED_TRACE(response);
        FakeMotionTransport transport;
        transport.responses = {response};
        MotionExecution execution(transport);
        EXPECT_NE(execution.execute({segment(1), segment(2)}), MotionExecutionResult::Success);
        EXPECT_EQ(execution.state(), MotionExecutionState::Error);
        transport.responses = {"ACM1|2|ACK", "ACM1|2|DONE"};
        EXPECT_EQ(execution.execute({segment(2)}), MotionExecutionResult::RecoveryRequired);
        EXPECT_EQ(transport.sent.size(), 1u);
    }
}

TEST(MotionExecutionTest, RejectsInvalidTrajectoryOrdering)
{
    FakeMotionTransport transport;
    MotionExecution execution(transport);

    EXPECT_THROW(
        (void)execution.execute({segment(2), segment(1)}),
        std::invalid_argument
    );
    EXPECT_TRUE(transport.sent.empty());
}

} // namespace
} // namespace ac::motion
