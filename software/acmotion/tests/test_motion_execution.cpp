#include <gtest/gtest.h>

#include <chrono>
#include <deque>
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

TEST(MotionExecutionTest, CancelSendsVersionedCancelFrame)
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

    ASSERT_TRUE(execution.cancel());
    EXPECT_EQ(execution.state(), MotionExecutionState::Cancelled);
    ASSERT_GE(transport.sent.size(), 2u);
    EXPECT_EQ(transport.sent.back(), "ACM1|7|CANCEL\n");
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
