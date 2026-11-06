#pragma once
#include <opencv2/objdetect/aruco_detector.hpp>
#include <opencv2/calib3d.hpp>
#include <opencv2/imgproc.hpp>
#include <array>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <cmath>

namespace ac {
// Each configured ID maps its four ArUco corners to rectified pixels.
struct BoardReference {
    std::map<int,std::array<cv::Point2f,4>> markers;
    double maxReprojectionErrorPx;
};
struct ReferenceObservation {
    cv::Mat imageToRectified;
    double maxReprojectionErrorPx;
};
inline BoardReference loadBoardReference(const std::string& path) {
    cv::FileStorage fs(path,cv::FileStorage::READ);
    if (!fs.isOpened() || (int)fs["schema"]!=1 ||
        (std::string)fs["dictionary"]!="DICT_4X4_50" ||
        (std::string)fs["orientation"]!="a8_top_left" || (int)fs["rectified_size"]!=800)
        throw std::invalid_argument("Invalid reference file");
    BoardReference result{{},(double)fs["max_reprojection_error_rectified_px"]};
    const auto markers=fs["markers"];
    if (!markers.isSeq() || markers.size()!=4) throw std::invalid_argument("Four markers required");
    for (const auto& marker:markers) {
        if (!marker["id"].isInt()) throw std::invalid_argument("Integer ID required");
        int id=(int)marker["id"];
        const auto points=marker["corners_rectified_px"];
        if (!points.isSeq() || points.size()!=4) throw std::invalid_argument("Four corners required");
        std::array<cv::Point2f,4> corners;
        for (int i=0;i<4;++i) {
            if (!points[i].isSeq() || points[i].size()!=2) throw std::invalid_argument("XY required");
            corners[i]={(float)points[i][0],(float)points[i][1]};
        }
        if (!result.markers.emplace(id,corners).second) throw std::invalid_argument("Duplicate ID");
    }
    return result;
}
inline std::optional<ReferenceObservation> detectBoardReference(
    const cv::Mat& image,const BoardReference& reference,std::vector<int>* detectedIds=nullptr) {
    if(reference.markers.size()!=4 || !std::isfinite(reference.maxReprojectionErrorPx) ||
       reference.maxReprojectionErrorPx<=0) throw std::invalid_argument("Invalid reference configuration");

    for(const auto& entry:reference.markers) {
        if(entry.first<0 || entry.first>=50) throw std::invalid_argument("Marker ID outside DICT_4X4_50");
        for(const auto& p:entry.second) {
            if(!std::isfinite(p.x)||!std::isfinite(p.y)) throw std::invalid_argument("Nonfinite reference");

        }
        const std::vector<cv::Point2f> quad(entry.second.begin(),entry.second.end());
        if(!cv::isContourConvex(quad) || std::abs(cv::contourArea(quad))<1)
            throw std::invalid_argument("Degenerate reference marker");
    }
    if(image.empty() || image.type()!=CV_8UC3) return std::nullopt;
    cv::aruco::DetectorParameters parameters;
    parameters.cornerRefinementMethod=cv::aruco::CORNER_REFINE_SUBPIX;
    cv::aruco::ArucoDetector detector(cv::aruco::getPredefinedDictionary(cv::aruco::DICT_4X4_50),parameters);
    std::vector<int> ids;
    std::vector<std::vector<cv::Point2f>> corners;
    detector.detectMarkers(image,corners,ids);
    if(detectedIds) *detectedIds=ids;
    std::set<int> seen;
    std::vector<cv::Point2f> src,dst;
    for(size_t i=0;i<ids.size();++i) {
        auto it=reference.markers.find(ids[i]);
        if(it==reference.markers.end()) continue;
        if(!seen.insert(ids[i]).second) return std::nullopt;
        src.insert(src.end(),corners[i].begin(),corners[i].end());
        dst.insert(dst.end(),it->second.begin(),it->second.end());
    }
    if(seen.size()!=4) return std::nullopt;
    const auto H=cv::findHomography(src,dst,0);
    if(H.empty() || !cv::checkRange(H) || cv::determinant(H)==0) return std::nullopt;
    std::vector<cv::Point2f> projected;
    cv::perspectiveTransform(src,projected,H);
    double error=0;
    for(size_t i=0;i<dst.size();++i) error=std::max(error,cv::norm(projected[i]-dst[i]));
    if(error>reference.maxReprojectionErrorPx) return std::nullopt;
    return ReferenceObservation{H,error};
}
}
