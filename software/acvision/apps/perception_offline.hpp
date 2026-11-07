#pragma once
// Offline orchestration only. Perception algorithms remain in acvision.
#include "board_vision/board_vision.hpp"
#include "homography/homography.hpp"
#include "piece_detector/piece_detector.hpp"
#include "board_reference/board_reference.hpp"
#include <cmath>
#include <optional>
#include <stdexcept>
#include <string>

namespace ac::offline {
inline constexpr const char* configId = "acvision-defaults-800-v1";
inline std::string inputError(const cv::Mat& frame) {
    if (frame.empty()) return "EMPTY_OR_UNDECODABLE_IMAGE";
    if (frame.dims != 2 || frame.rows < 27 || frame.cols < 27)
        return "INVALID_DIMENSIONS"; // cornerSubPix window: 2*11+5 pixels minimum.
    if (frame.channels() != 3) return "UNSUPPORTED_CHANNELS";
    if (frame.depth() != CV_8U) return "UNSUPPORTED_DEPTH";
    return {};
}
inline std::string cornerError(const std::array<cv::Point2f,4>& corners, cv::Size size) {
    for (size_t i=0;i<4;++i) {
        auto p = corners[i];
        if (!std::isfinite(p.x) || !std::isfinite(p.y)) return "NONFINITE_CORNERS";
        if (p.x < 0 || p.y < 0 || p.x >= size.width || p.y >= size.height) return "CORNERS_OUTSIDE_IMAGE";
        for (size_t j=0;j<i;++j) if (p == corners[j]) return "REPEATED_CORNERS";
    }
    const std::vector<cv::Point2f> polygon(corners.begin(),corners.end());
    // Less than one source pixel of area cannot support this raster diagnostic.
    if (std::abs(cv::contourArea(polygon)) < 1.) return "INSUFFICIENT_PIXEL_AREA";
    if (!cv::isContourConvex(polygon)) return "NONCONVEX_CORNERS";
    return {};
}
struct Result {
    std::optional<BoardCorners> detected;
    cv::Mat homography, rectified;
    std::optional<BoardObservation> observation;
    std::string geometryError;
    bool referenceOriented=false;
    double referenceResidual=0;
    std::vector<int> detectedReferenceIds;
};
inline Result process(const cv::Mat& bgr,const BoardReference* reference=nullptr) {
    const auto error = inputError(bgr);
    if (!error.empty()) throw std::invalid_argument(error);
    Result result;
    if(reference) {
        const auto found=detectBoardReference(bgr,*reference,&result.detectedReferenceIds);
        if(!found) { result.geometryError="REFERENCE_NOT_VISIBLE_OR_INCONSISTENT"; return result; }
        result.homography=found->imageToRectified;
        result.referenceResidual=found->maxReprojectionErrorPx;
        std::vector<cv::Point2f> corners;
        cv::perspectiveTransform(std::vector<cv::Point2f>{{0,0},{800,0},{800,800},{0,800}},corners,result.homography.inv());
        result.detected=BoardCorners{{corners[0],corners[1],corners[2],corners[3]}};
        result.referenceOriented=true;
    } else {
        result.detected = BoardDetector().detect(bgr);
        if (!result.detected) return result;
        result.homography = Homography().compute(result.detected->corners);
    }
    result.geometryError = cornerError(result.detected->corners,bgr.size());
    if (!result.geometryError.empty()) { result.homography.release(); result.referenceOriented=false; return result; }
    if (!cv::checkRange(result.homography) || cv::determinant(result.homography) == 0) {
        result.geometryError = "INVALID_HOMOGRAPHY";
        result.homography.release();
        return result;
    }
    result.rectified = Homography().warp(bgr,result.homography,800);
    std::array<std::array<cv::Mat,8>,8> cells;
    for (int r=0;r<8;++r) for (int c=0;c<8;++c)
        cells[r][c] = result.rectified(cv::Rect(c*100,r*100,100,100));
    result.observation = PieceDetector().analyzeBoard(cells);
    return result;
}
} // namespace ac::offline
