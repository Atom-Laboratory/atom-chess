#ifndef AC_PIECE_DETECTOR_CONFIG_HPP
#define AC_PIECE_DETECTOR_CONFIG_HPP

#include <opencv2/core.hpp>

#include <iostream>
#include <string>

namespace ac {

/**
 * @struct ColorProfile
 * @brief HSV boundaries used to classify an observed piece color.
 */
struct ColorProfile {
    cv::Scalar lowerBound{};
    cv::Scalar upperBound{};
};

/**
 * @struct PieceDetectorConfig
 * @brief Optional persistent configuration for PieceDetector color calibration.
 *
 * Calibration is intentionally optional. If no valid configuration is loaded,
 * PieceDetector keeps using its default brightness-based classifier.
 */
struct PieceDetectorConfig {
    bool useCalibration{false};
    ColorProfile whiteProfile{};
    ColorProfile blackProfile{};

    bool save(const std::string& filename) const
    {
        cv::FileStorage storage(filename, cv::FileStorage::WRITE);
        if (!storage.isOpened()) {
            std::cerr << "[ACVISION][ERROR] Cannot write calibration file: "
                      << filename << '\n';
            return false;
        }

        storage << "version" << 1;
        storage << "useCalibration" << static_cast<int>(useCalibration);
        storage << "whiteProfile_lower" << whiteProfile.lowerBound;
        storage << "whiteProfile_upper" << whiteProfile.upperBound;
        storage << "blackProfile_lower" << blackProfile.lowerBound;
        storage << "blackProfile_upper" << blackProfile.upperBound;
        return true;
    }

    bool load(const std::string& filename)
    {
        cv::FileStorage storage(filename, cv::FileStorage::READ);
        if (!storage.isOpened()) {
            return false;
        }

        int version = 0;
        int enabled = 0;
        storage["version"] >> version;
        storage["useCalibration"] >> enabled;
        storage["whiteProfile_lower"] >> whiteProfile.lowerBound;
        storage["whiteProfile_upper"] >> whiteProfile.upperBound;
        storage["blackProfile_lower"] >> blackProfile.lowerBound;
        storage["blackProfile_upper"] >> blackProfile.upperBound;

        const auto validProfile = [](const ColorProfile& profile) {
            const double maxValues[4] = {180.0, 255.0, 255.0, 0.0};
            for (int i = 0; i < 3; ++i) {
                if (profile.lowerBound[i] < 0.0 ||
                    profile.upperBound[i] > maxValues[i] ||
                    profile.lowerBound[i] > profile.upperBound[i]) {
                    return false;
                }
            }
            return true;
        };

        if (version != 1 ||
            !validProfile(whiteProfile) ||
            !validProfile(blackProfile)) {
            useCalibration = false;
            return false;
        }

        useCalibration = enabled != 0;
        return true;
    }
};

} // namespace ac

#endif
