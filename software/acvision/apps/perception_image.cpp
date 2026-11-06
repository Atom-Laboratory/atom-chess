// Image-only executable: no simulator, controller or policy dependency.
#include "perception_offline.hpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <cstdint>
#include <iterator>
#ifndef ACVISION_SOURCE_SHA256
#define ACVISION_SOURCE_SHA256 "unavailable"
#endif
namespace {
std::string quote(const std::string& value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c);
        else out << c;
    }
    return out.str()+'"';
}
std::string fingerprint(const std::vector<unsigned char>& bytes) {
    uint64_t hash = 14695981039346656037ULL;
    for (auto b : bytes) { hash ^= b; hash *= 1099511628211ULL; }
    std::ostringstream out;
    out << "fnv1a64:" << std::hex << std::setfill('0') << std::setw(16) << hash;
    return out.str(); // Content identity only; not a cryptographic security check.
}
void save(const std::filesystem::path& path,const cv::Mat& image) {
    if (!cv::imwrite(path.string(),image)) throw std::runtime_error("OVERLAY_WRITE_FAILED");
}
}
int main(int argc,char** argv) {
    if (argc != 3 && argc != 5) {
        std::cerr << "Usage: perception_image IMAGE NEW_OUTPUT [--config acvision-defaults-800-v1]\n";
        return 2;
    }
    const std::filesystem::path out(argv[2]);
    try {
        if (!std::filesystem::create_directory(out)) throw std::runtime_error("OUTPUT_EXISTS");
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n'; return 2;
    }
    cv::Mat frame;
    ac::offline::Result result;
    std::string error, detail, imageId;
    std::string config = argc == 5 ? argv[4] : ac::offline::configId;
    bool completed=false, rawSaved=false, gridSaved=false, rectifiedSaved=false;
    size_t byteCount=0;
    try {
        if ((argc == 5 && std::string(argv[3]) != "--config") || config != ac::offline::configId)
            throw std::invalid_argument("INVALID_CONFIGURATION");
        std::ifstream file(argv[1],std::ios::binary);
        if (!file) throw std::invalid_argument("IMAGE_NOT_READABLE");
        const std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(file)),{});
        imageId=fingerprint(bytes); byteCount=bytes.size();
        if (bytes.empty()) throw std::invalid_argument("EMPTY_IMAGE_FILE");
        // File decoder produces BGR. Preserve depth/channels to validate, not coerce.
        frame=cv::imdecode(bytes,cv::IMREAD_UNCHANGED);
        const auto invalid=ac::offline::inputError(frame);
        if (!invalid.empty()) throw std::invalid_argument(invalid);
        result=ac::offline::process(frame);
        auto raw=frame.clone();
        if (result.detected) for(int i=0;i<4;++i) {
            auto p=result.detected->corners[i];
            if (!std::isfinite(p.x)||!std::isfinite(p.y)||p.x<0||p.y<0||p.x>=frame.cols||p.y>=frame.rows) continue;
            cv::circle(raw,p,4,cv::Scalar(0,255,0),2);
            cv::putText(raw,std::to_string(i),p,cv::FONT_HERSHEY_SIMPLEX,.7,cv::Scalar(0,0,255),2);
            if (result.geometryError.empty()) cv::line(raw,p,result.detected->corners[(i+1)%4],cv::Scalar(0,255,0),2);
        }
        save(out/"corners.png",raw); rawSaved=true;
        if (result.observation) {
            save(out/"rectified.png",result.rectified); rectifiedSaved=true;
            auto grid=result.rectified.clone();
            for(int r=0;r<8;++r) for(int c=0;c<8;++c) {
                cv::rectangle(grid,cv::Rect(c*100,r*100,100,100),cv::Scalar(0,200,0),1);
                cv::putText(grid,std::to_string(r)+","+std::to_string(c),cv::Point(c*100+3,r*100+20),
                    cv::FONT_HERSHEY_SIMPLEX,.4,cv::Scalar(0,0,255),1);
            }
            save(out/"rectified-grid.png",grid); gridSaved=true;
        }
        completed=true;
    } catch (const std::invalid_argument& e) { error=e.what(); }
      catch (const std::exception& e) { error="PROCESSING_OR_EXPORT_FAILED"; detail=e.what(); }
    try {
        // Completion is published only after successful artifact export.
        std::ofstream json(out/"observation.json");
        json.exceptions(std::ios::badbit|std::ios::failbit);
        json << std::setprecision(17) << std::boolalpha;
        json << "{\"schema_version\":2,\"implementation\":\"acvision_cpp\",\"source_sha256\":" << quote(ACVISION_SOURCE_SHA256)
             << ",\"opencv_version\":" << quote(CV_VERSION)
             << ",\"image_path\":" << quote(std::filesystem::absolute(argv[1]).generic_u8string())
             << ",\"image_id\":" << (imageId.empty()?"null":quote(imageId)) << ",\"image_bytes\":" << byteCount
             << ",\"image_width\":" << frame.cols << ",\"image_height\":" << frame.rows
             << ",\"decoded_channels\":" << (frame.empty()?0:frame.channels())
             << ",\"input_color\":" << (frame.type()==CV_8UC3&&!frame.empty()?"\"BGR\"":"null")
             << ",\"configuration_id\":" << quote(config) << ",\"processing_completed\":" << completed
             << ",\"status\":" << quote(completed?"completed":"failed")
             << ",\"board_detection_status\":" << quote(!result.detected?(completed?"not_detected":"not_run"):
                    result.geometryError.empty()?"unvalidated_candidate":"rejected_geometry")
             << ",\"orientation\":\"unknown\",\"calibration_status\":\"absent\",\"perception_valid\":false,"
             << "\"motion_ready\":false,\"confidence\":null,\"gripper_pose\":null,\"corners_px\":";
        if (!result.detected) json << "null";
        else {
            json << '[';
            for(int i=0;i<4;++i) {
                if(i) json << ',';
                auto p=result.detected->corners[i];
                if(std::isfinite(p.x)&&std::isfinite(p.y)) json << '[' << p.x << ',' << p.y << ']';
                else json << "null";
            }
            json << ']';
        }
        json << ",\"homography\":";
        if(result.homography.empty()) json << "null";
        else {
            json << '[';
            for(int r=0;r<3;++r) {
                if(r) json << ',';
                json << '[' << result.homography.at<double>(r,0) << ',' << result.homography.at<double>(r,1)
                     << ',' << result.homography.at<double>(r,2) << ']';
            }
            json << ']';
        }
        json << ",\"homography_geometry\":{\"direction\":\"original_image_to_rectified\",\"units\":\"pixels\","
             << "\"corner_order\":[\"TL\",\"TR\",\"BR\",\"BL\"],\"destination_corners\":[[0,0],[800,0],[800,800],[0,800]],"
             << "\"rectified_size\":[800,800],\"undistorted\":false},\"cells\":[";
        if(result.observation) for(int r=0;r<8;++r) for(int c=0;c<8;++c) {
            if(r||c) json << ',';
            auto state=result.observation->cells[r][c];
            const char* label=state==ac::CellObservationState::EMPTY?"empty":state==ac::CellObservationState::WHITE?"white":"black";
            json << "{\"row\":" << r << ",\"column\":" << c << ",\"square\":null,\"candidate\":" << quote(label)
                 << ",\"occupancy\":\"unknown\",\"confidence\":null,\"visibility\":\"unknown\",\"piece_center\":null}";
        }
        json << "],\"overlays\":{\"raw_corners\":" << (rawSaved?"\"corners.png\"":"null")
             << ",\"rectified\":" << (rectifiedSaved?"\"rectified.png\"":"null")
             << ",\"rectified_grid\":" << (gridSaved?"\"rectified-grid.png\"":"null") << "},\"errors\":[";
        if(!error.empty()) json << "{\"code\":" << quote(error) << ",\"detail\":" << quote(detail) << '}';
        json << "],\"warnings\":[\"ORIENTATION_UNKNOWN\",\"NO_OPTICAL_OR_METRIC_CALIBRATION\","
             << "\"CANDIDATES_NOT_VERIFIED_OCCUPANCY\",\"RECTANGLE_FALSE_POSITIVES_POSSIBLE\"";
        if(!result.geometryError.empty()) json << ',' << quote(result.geometryError);
        json << "]}\n";
        json.close();
    } catch(const std::exception& e) { std::cerr << e.what() << '\n'; return 2; }
    return completed?0:2;
}
