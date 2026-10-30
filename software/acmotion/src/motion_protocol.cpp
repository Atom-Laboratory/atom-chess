#include "motion/motion_protocol.hpp"

#include <charconv>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <system_error>
#include <vector>

namespace ac::motion {
namespace {

/**
 * @brief Removes trailing CR/LF characters from one received protocol line.
 * @param line Raw line from the transport.
 * @return Normalized line without trailing line terminators.
 */
std::string trimLineEndings(std::string line)
{
    while (!line.empty()
           && (line.back() == '\n' || line.back() == '\r')) {
        line.pop_back();
    }
    return line;
}

/**
 * @brief Splits a protocol line by the ACM1 field delimiter.
 * @param line Normalized line.
 * @return Ordered string-view fields referencing line.
 */
std::vector<std::string_view> splitFields(const std::string& line)
{
    std::vector<std::string_view> fields;
    std::size_t begin = 0;

    while (begin <= line.size()) {
        const std::size_t end = line.find('|', begin);
        if (end == std::string::npos) {
            fields.emplace_back(line.data() + begin, line.size() - begin);
            break;
        }

        fields.emplace_back(line.data() + begin, end - begin);
        begin = end + 1;
    }

    return fields;
}

/**
 * @brief Parses a complete unsigned 32-bit decimal field.
 */
/**
 * @brief Parses a complete unsigned 32-bit decimal protocol field.
 * @param field Character range to parse.
 * @return Parsed value, or std::nullopt when any character/range is invalid.
 */
std::optional<std::uint32_t> parseUint32(std::string_view field)
{
    std::uint32_t value = 0;
    const char* begin = field.data();
    const char* end = field.data() + field.size();
    const auto [ptr, error] = std::from_chars(begin, end, value);

    if (error != std::errc{} || ptr != end) {
        return std::nullopt;
    }

    return value;
}

/**
 * @brief Parses a complete signed decimal integer field.
 */
/**
 * @brief Parses a complete signed decimal protocol field.
 * @param field Character range to parse.
 * @return Parsed value, or std::nullopt when any character/range is invalid.
 */
std::optional<int> parseInt(std::string_view field)
{
    int value = 0;
    const char* begin = field.data();
    const char* end = field.data() + field.size();
    const auto [ptr, error] = std::from_chars(begin, end, value);

    if (error != std::errc{} || ptr != end) {
        return std::nullopt;
    }

    return value;
}

} // namespace

/**
 * @brief Enforces protocol-level segment invariants before serialization.
 */
void MotionProtocol::validateSegment(const JointSegment& segment)
{
    const JointTarget& target = segment.target;

    if (segment.sequence == 0) {
        throw std::invalid_argument("Motion segment sequence must be non-zero");
    }

    if (segment.durationMs == 0) {
        throw std::invalid_argument("Motion segment duration must be non-zero");
    }

    if (!std::isfinite(target.joint1Rad)
        || !std::isfinite(target.joint2Rad)
        || !std::isfinite(target.joint3Rad)
        || !std::isfinite(target.zMm)
        || !std::isfinite(target.gripperPercent)) {
        throw std::invalid_argument("Motion segment target must be finite");
    }

    if (target.gripperPercent < 0.0 || target.gripperPercent > 100.0) {
        throw std::invalid_argument(
            "Gripper percentage must be inside [0, 100]"
        );
    }
}

/**
 * @brief Serializes a validated segment into one newline-terminated ACM1 frame.
 */
std::string MotionProtocol::encodeSegment(const JointSegment& segment)
{
    validateSegment(segment);

    std::ostringstream stream;
    stream << std::fixed << std::setprecision(6)
           << "ACM1|" << segment.sequence
           << "|SEG|" << segment.target.joint1Rad
           << '|' << segment.target.joint2Rad
           << '|' << segment.target.joint3Rad
           << '|' << segment.target.zMm
           << '|' << segment.target.gripperPercent
           << '|' << segment.durationMs
           << '\n';

    return stream.str();
}

/**
 * @brief Serializes explicit host cancellation for one non-zero sequence.
 */
std::string MotionProtocol::encodeCancel(std::uint32_t sequence)
{
    if (sequence == 0) {
        throw std::invalid_argument("Cancel sequence must be non-zero");
    }

    return "ACM1|" + std::to_string(sequence) + "|CANCEL\n";
}

/**
 * @brief Parses ACK/DONE/ERR/ESTOP/LIMIT controller frames for ACM1.
 *
 * Unknown versions, malformed fields and invalid sequence identifiers are
 * rejected with std::nullopt.
 */
std::optional<ControllerEvent> MotionProtocol::parseEvent(
    const std::string& rawLine)
{
    const std::string line = trimLineEndings(rawLine);
    const auto fields = splitFields(line);

    if (fields.size() < 3 || fields[0] != "ACM1") {
        return std::nullopt;
    }

    const auto sequence = parseUint32(fields[1]);
    if (!sequence.has_value() || *sequence == 0) {
        return std::nullopt;
    }

    if (fields[2] == "ACK" && fields.size() == 3) {
        return ControllerEvent{ControllerEventType::Ack, *sequence, 0};
    }

    if (fields[2] == "DONE" && fields.size() == 3) {
        return ControllerEvent{ControllerEventType::Done, *sequence, 0};
    }

    if (fields[2] == "ESTOP" && fields.size() == 3) {
        return ControllerEvent{
            ControllerEventType::EmergencyStop,
            *sequence,
            0
        };
    }

    if (fields[2] == "LIMIT" && fields.size() == 3) {
        return ControllerEvent{
            ControllerEventType::LimitTriggered,
            *sequence,
            0
        };
    }

    if (fields[2] == "ERR" && fields.size() == 4) {
        const auto code = parseInt(fields[3]);
        if (!code.has_value()) {
            return std::nullopt;
        }

        return ControllerEvent{
            ControllerEventType::Error,
            *sequence,
            *code
        };
    }

    return std::nullopt;
}

} // namespace ac::motion
