#include <gtest/gtest.h>

#include <limits>

#include "motion/motion_protocol.hpp"

namespace ac::motion {
namespace {

TEST(MotionProtocolTest, EncodesVersionedJointSegment)
{
    const JointSegment segment{
        42,
        {0.5, -0.25, 25.0, 80.0},
        750
    };

    EXPECT_EQ(
        MotionProtocol::encodeSegment(segment),
        "ACM1|42|SEG|0.500000|-0.250000|25.000000|80.000000|750\n"
    );
}

TEST(MotionProtocolTest, EncodesCancelFrame)
{
    EXPECT_EQ(
        MotionProtocol::encodeCancel(9),
        "ACM1|9|CANCEL\n"
    );
}

TEST(MotionProtocolTest, ParsesControllerEvents)
{
    const auto ack = MotionProtocol::parseEvent("ACM1|4|ACK\r\n");
    const auto done = MotionProtocol::parseEvent("ACM1|4|DONE\n");
    const auto error = MotionProtocol::parseEvent("ACM1|4|ERR|17\n");
    const auto estop = MotionProtocol::parseEvent("ACM1|4|ESTOP\n");
    const auto limit = MotionProtocol::parseEvent("ACM1|4|LIMIT\n");

    ASSERT_TRUE(ack.has_value());
    ASSERT_TRUE(done.has_value());
    ASSERT_TRUE(error.has_value());
    ASSERT_TRUE(estop.has_value());
    ASSERT_TRUE(limit.has_value());

    EXPECT_EQ(ack->type, ControllerEventType::Ack);
    EXPECT_EQ(done->type, ControllerEventType::Done);
    EXPECT_EQ(error->type, ControllerEventType::Error);
    EXPECT_EQ(error->errorCode, 17);
    EXPECT_EQ(estop->type, ControllerEventType::EmergencyStop);
    EXPECT_EQ(limit->type, ControllerEventType::LimitTriggered);
}

TEST(MotionProtocolTest, RejectsMalformedOrUnsupportedFrames)
{
    EXPECT_FALSE(MotionProtocol::parseEvent("garbage").has_value());
    EXPECT_FALSE(MotionProtocol::parseEvent("ACM2|1|ACK").has_value());
    EXPECT_FALSE(MotionProtocol::parseEvent("ACM1|0|ACK").has_value());
    EXPECT_FALSE(MotionProtocol::parseEvent("ACM1|1|ERR|abc").has_value());
    EXPECT_FALSE(MotionProtocol::parseEvent("ACM1|1|UNKNOWN").has_value());
}

TEST(MotionProtocolTest, RejectsInvalidSegment)
{
    JointSegment segment{
        1,
        {0.0, 0.0, 0.0, 101.0},
        500
    };

    EXPECT_THROW(
        (void)MotionProtocol::encodeSegment(segment),
        std::invalid_argument
    );

    segment.target.gripperPercent = 50.0;
    segment.target.joint1Rad =
        std::numeric_limits<double>::quiet_NaN();

    EXPECT_THROW(
        (void)MotionProtocol::encodeSegment(segment),
        std::invalid_argument
    );
}

} // namespace
} // namespace ac::motion
