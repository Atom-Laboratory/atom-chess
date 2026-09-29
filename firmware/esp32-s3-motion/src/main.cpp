#include <Arduino.h>
#include <AccelStepper.h>
#include <ESP32Servo.h>

#include "robot_config.hpp"

namespace {

/**
 * @brief Error codes returned through ACM1 ERR frames.
 */
enum class ErrorCode : int {
    InvalidFrame = 1,
    InvalidNumber = 2,
    NotConfigured = 100,
    EmergencyStop = 101,
    LimitTriggered = 102
};

AccelStepper j1(AccelStepper::DRIVER,
                atom_motion_config::j1StepPin,
                atom_motion_config::j1DirPin);
AccelStepper j2(AccelStepper::DRIVER,
                atom_motion_config::j2StepPin,
                atom_motion_config::j2DirPin);
AccelStepper j3(AccelStepper::DRIVER,
                atom_motion_config::j3StepPin,
                atom_motion_config::j3DirPin);
AccelStepper zAxis(AccelStepper::DRIVER,
                   atom_motion_config::zStepPin,
                   atom_motion_config::zDirPin);
Servo gripper;

/**
 * @brief Returns whether a configurable digital input is active.
 * @param pin GPIO number, or a negative value when the input is unavailable.
 * @param activeLow Whether LOW means asserted.
 * @return true when the configured input is asserted.
 */
bool inputActive(int pin, bool activeLow)
{
    if (pin < 0) {
        return false;
    }

    const int level = digitalRead(pin);
    return activeLow ? level == LOW : level == HIGH;
}

/**
 * @brief Sends one ACM1 response event.
 * @param sequence Host command sequence.
 * @param event ACK, DONE, ESTOP or LIMIT.
 */
void sendEvent(unsigned long sequence, const char* event)
{
    Serial.printf("ACM1|%lu|%s\n", sequence, event);
}

/**
 * @brief Sends one ACM1 error response.
 * @param sequence Host command sequence, zero if frame sequence could not be parsed.
 * @param code Numeric firmware error code.
 */
void sendError(unsigned long sequence, ErrorCode code)
{
    Serial.printf(
        "ACM1|%lu|ERR|%d\n",
        sequence,
        static_cast<int>(code)
    );
}

/**
 * @brief Splits one mutable protocol line in-place.
 * @param line NUL-terminated frame buffer.
 * @param fields Output token pointers.
 * @param maxFields Capacity of fields.
 * @return Number of tokens produced.
 */
size_t splitFields(char* line, char** fields, size_t maxFields)
{
    size_t count = 0;
    char* save = nullptr;
    char* token = strtok_r(line, "|", &save);

    while (token != nullptr && count < maxFields) {
        fields[count++] = token;
        token = strtok_r(nullptr, "|", &save);
    }

    return count;
}

/**
 * @brief Parses a complete finite floating-point field.
 */
bool parseDouble(const char* text, double& value)
{
    char* end = nullptr;
    value = strtod(text, &end);
    return end != text && *end == '\0' && isfinite(value);
}

/**
 * @brief Parses a complete unsigned integer field.
 */
bool parseUnsigned(const char* text, unsigned long& value)
{
    char* end = nullptr;
    value = strtoul(text, &end, 10);
    return end != text && *end == '\0';
}

/**
 * @brief Converts gripper percentage to calibrated servo pulse width.
 */
int gripperPulse(double percent)
{
    const double clamped = constrain(percent, 0.0, 100.0);
    return static_cast<int>(
        atom_motion_config::servoMinUs
        + (atom_motion_config::servoMaxUs - atom_motion_config::servoMinUs)
          * clamped / 100.0
    );
}

/**
 * @brief Stops all four stepper axes immediately.
 */
void stopAxes()
{
    j1.stop();
    j2.stop();
    j3.stop();
    zAxis.stop();
}

/**
 * @brief Returns true when any configured mechanical limit is asserted.
 */
bool anyLimitActive()
{
    return inputActive(
               atom_motion_config::j1LimitPin,
               atom_motion_config::limitsActiveLow
           )
        || inputActive(
               atom_motion_config::j2LimitPin,
               atom_motion_config::limitsActiveLow
           )
        || inputActive(
               atom_motion_config::j3LimitPin,
               atom_motion_config::limitsActiveLow
           )
        || inputActive(
               atom_motion_config::zLimitPin,
               atom_motion_config::limitsActiveLow
           );
}

/**
 * @brief Executes one four-axis joint target after ACM1 validation.
 *
 * This is intentionally a conservative blocking MVP executor. Each axis uses
 * AccelStepper acceleration limits. Future synchronized profiles may replace
 * this implementation without changing the host chess-domain boundary.
 */
bool executeSegment(
    unsigned long sequence,
    double j1Rad,
    double j2Rad,
    double j3Rad,
    double zMm,
    double gripperPercent,
    unsigned long durationMs)
{
    if (!atom_motion_config::configured) {
        sendError(sequence, ErrorCode::NotConfigured);
        return false;
    }

    if (inputActive(
            atom_motion_config::emergencyStopPin,
            atom_motion_config::emergencyStopActiveLow)) {
        sendEvent(sequence, "ESTOP");
        return false;
    }

    const long j1Target = lround(j1Rad * atom_motion_config::j1StepsPerRad);
    const long j2Target = lround(j2Rad * atom_motion_config::j2StepsPerRad);
    const long j3Target = lround(j3Rad * atom_motion_config::j3StepsPerRad);
    const long zTarget = lround(zMm * atom_motion_config::zStepsPerMm);

    j1.moveTo(j1Target);
    j2.moveTo(j2Target);
    j3.moveTo(j3Target);
    zAxis.moveTo(zTarget);

    const double durationSeconds = max(0.001, durationMs / 1000.0);
    const auto setSegmentSpeed = [durationSeconds](AccelStepper& axis) {
        const double required =
            abs(axis.distanceToGo()) / durationSeconds;
        axis.setMaxSpeed(
            min(required, atom_motion_config::maxStepperSpeed)
        );
    };

    setSegmentSpeed(j1);
    setSegmentSpeed(j2);
    setSegmentSpeed(j3);
    setSegmentSpeed(zAxis);

    gripper.writeMicroseconds(gripperPulse(gripperPercent));

    sendEvent(sequence, "ACK");

    while (j1.distanceToGo() != 0
           || j2.distanceToGo() != 0
           || j3.distanceToGo() != 0
           || zAxis.distanceToGo() != 0) {
        if (inputActive(
                atom_motion_config::emergencyStopPin,
                atom_motion_config::emergencyStopActiveLow)) {
            stopAxes();
            sendEvent(sequence, "ESTOP");
            return false;
        }

        if (anyLimitActive()) {
            stopAxes();
            sendEvent(sequence, "LIMIT");
            return false;
        }

        j1.run();
        j2.run();
        j3.run();
        zAxis.run();
        yield();
    }

    sendEvent(sequence, "DONE");
    return true;
}

/**
 * @brief Parses and dispatches one complete ACM1 line.
 */
void handleFrame(char* line)
{
    char* fields[10]{};
    const size_t count = splitFields(line, fields, 10);

    if (count < 3 || strcmp(fields[0], "ACM1") != 0) {
        sendError(0, ErrorCode::InvalidFrame);
        return;
    }

    unsigned long sequence = 0;
    if (!parseUnsigned(fields[1], sequence) || sequence == 0) {
        sendError(0, ErrorCode::InvalidNumber);
        return;
    }

    if (strcmp(fields[2], "CANCEL") == 0 && count == 3) {
        stopAxes();
        sendEvent(sequence, "DONE");
        return;
    }

    // ACM1|seq|SEG|j1|j2|j3|z|gripper|duration
    if (strcmp(fields[2], "SEG") != 0 || count != 9) {
        sendError(sequence, ErrorCode::InvalidFrame);
        return;
    }

    double j1Rad = 0.0;
    double j2Rad = 0.0;
    double j3Rad = 0.0;
    double zMm = 0.0;
    double gripperPercent = 0.0;
    unsigned long durationMs = 0;

    if (!parseDouble(fields[3], j1Rad)
        || !parseDouble(fields[4], j2Rad)
        || !parseDouble(fields[5], j3Rad)
        || !parseDouble(fields[6], zMm)
        || !parseDouble(fields[7], gripperPercent)
        || !parseUnsigned(fields[8], durationMs)
        || durationMs == 0
        || gripperPercent < 0.0
        || gripperPercent > 100.0) {
        sendError(sequence, ErrorCode::InvalidNumber);
        return;
    }

    (void)executeSegment(
        sequence,
        j1Rad,
        j2Rad,
        j3Rad,
        zMm,
        gripperPercent,
        durationMs
    );
}

} // namespace

void setup()
{
    Serial.begin(115200);

    const auto configureInput = [](int pin) {
        if (pin >= 0) {
            pinMode(pin, INPUT_PULLUP);
        }
    };

    configureInput(atom_motion_config::j1LimitPin);
    configureInput(atom_motion_config::j2LimitPin);
    configureInput(atom_motion_config::j3LimitPin);
    configureInput(atom_motion_config::zLimitPin);
    configureInput(atom_motion_config::emergencyStopPin);

    j1.setPinsInverted(atom_motion_config::j1InvertDirection);
    j2.setPinsInverted(atom_motion_config::j2InvertDirection);
    j3.setPinsInverted(atom_motion_config::j3InvertDirection);
    zAxis.setPinsInverted(atom_motion_config::zInvertDirection);

    for (AccelStepper* axis : {&j1, &j2, &j3, &zAxis}) {
        axis->setMaxSpeed(atom_motion_config::maxStepperSpeed);
        axis->setAcceleration(atom_motion_config::stepperAcceleration);
    }

    if (atom_motion_config::gripperServoPin >= 0) {
        gripper.attach(
            atom_motion_config::gripperServoPin,
            atom_motion_config::servoMinUs,
            atom_motion_config::servoMaxUs
        );
    }

    Serial.println(
        atom_motion_config::configured
            ? "ATOM_MOTION_READY"
            : "ATOM_MOTION_CONFIG_REQUIRED"
    );
}

void loop()
{
    static char line[192];
    static size_t used = 0;

    while (Serial.available() > 0) {
        const char ch = static_cast<char>(Serial.read());

        if (ch == '\n') {
            line[used] = '\0';
            if (used > 0 && line[used - 1] == '\r') {
                line[used - 1] = '\0';
            }
            handleFrame(line);
            used = 0;
            continue;
        }

        if (used + 1 < sizeof(line)) {
            line[used++] = ch;
        } else {
            used = 0;
            sendError(0, ErrorCode::InvalidFrame);
        }
    }
}
