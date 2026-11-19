#pragma once

#include <opencv2/imgproc.hpp>
#include <array>
#include <optional>

namespace ac {

using ForegroundCenters = std::array<std::array<std::optional<cv::Point2d>, 8>, 8>;

// Diagnostic on the adapter's canonical 800 x 800 BGR board images.
inline ForegroundCenters locateForeground(const cv::Mat& current, const cv::Mat& empty)
{
    CV_Assert(current.size() == cv::Size(800, 800) && current.type() == CV_8UC3);
    CV_Assert(empty.size() == current.size() && empty.type() == current.type());

    cv::Mat difference, foreground;
    cv::absdiff(current, empty, difference);
    cv::inRange(difference, cv::Scalar(0, 0, 0), cv::Scalar(35, 35, 35), foreground);
    cv::bitwise_not(foreground, foreground);
    const auto kernel = cv::getStructuringElement(cv::MORPH_ELLIPSE, {5, 5});
    cv::morphologyEx(foreground, foreground, cv::MORPH_OPEN, kernel);

    cv::Mat labels, stats, centroids;
    const int count = cv::connectedComponentsWithStats(foreground, labels, stats, centroids);
    ForegroundCenters centers{};
    std::array<std::array<bool, 8>, 8> ambiguous{};
    for (int i = 1; i < count; ++i) {
        if (stats.at<int>(i, cv::CC_STAT_AREA) < 200) continue;

        const int left = stats.at<int>(i, cv::CC_STAT_LEFT);
        const int top = stats.at<int>(i, cv::CC_STAT_TOP);
        const int right = left + stats.at<int>(i, cv::CC_STAT_WIDTH) - 1;
        const int bottom = top + stats.at<int>(i, cv::CC_STAT_HEIGHT) - 1;
        const int row = top / 100;
        const int col = left / 100;
        // Also reject components clipped by an outer edge of the board.
        if (right / 100 != col || bottom / 100 != row ||
            left == 0 || top == 0 || right == 799 || bottom == 799) {
            for (int r = row; r <= bottom / 100; ++r)
                for (int c = col; c <= right / 100; ++c)
                    ambiguous[r][c] = true;
            continue;
        }
        if (centers[row][col]) ambiguous[row][col] = true;
        centers[row][col] = cv::Point2d(centroids.at<double>(i, 0), centroids.at<double>(i, 1));
    }

    for (int r = 0; r < 8; ++r)
        for (int c = 0; c < 8; ++c)
            if (ambiguous[r][c]) centers[r][c].reset();

    return centers;
}

} // namespace ac
