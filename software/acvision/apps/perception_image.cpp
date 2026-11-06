// Offline diagnostic boundary: actual acvision, no simulator inputs.
#include "board_vision/board_vision.hpp"
#include "homography/homography.hpp"
#include "piece_detector/piece_detector.hpp"
#include <opencv2/opencv.hpp>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "Usage: perception_image INPUT_IMAGE NEW_OUTPUT_DIRECTORY\n";
        return 2;
    }
    try {
        const auto frame = cv::imread(argv[1], cv::IMREAD_COLOR);
        if (frame.empty()) throw std::runtime_error("Unreadable image");
        const std::filesystem::path out(argv[2]);
        if (!std::filesystem::create_directory(out))
            throw std::runtime_error("Output already exists; preserve prior results");
        std::ofstream json(out / "observation.json");
        json.exceptions(std::ios::badbit | std::ios::failbit);
        json << std::setprecision(17);
        json << "{\"schema\":1,\"implementation\":\"acvision_cpp\","
             << "\"image_width\":" << frame.cols << ",\"image_height\":" << frame.rows
             << ",\"input_color\":\"BGR\",\"orientation\":\"unknown\","
             << "\"calibration_status\":\"unvalidated\",\"motion_ready\":false,"
             << "\"confidence\":null,\"gripper_pose\":null,";
        auto detected = ac::BoardDetector().detect(frame);
        cv::Mat overlay = frame.clone();
        cv::Mat H;
        bool valid = false;
        if (detected) {
            std::vector<cv::Point2f> points(detected->corners.begin(), detected->corners.end());
            valid = cv::isContourConvex(points) && std::abs(cv::contourArea(points)) > 1;
            for (const auto& p : points)
                valid = valid && std::isfinite(p.x) && std::isfinite(p.y)
                    && p.x >= 0 && p.y >= 0 && p.x < frame.cols && p.y < frame.rows;
            if (valid) {
                H = ac::Homography().compute(detected->corners);
                valid = cv::checkRange(H) && std::abs(cv::determinant(H)) > 1e-12;
            }
        }
        if (!valid) {
            json << "\"status\":\"no_valid_board_candidate\",\"corners_px\":null,"
                 << "\"homography\":null,\"cells\":[]}\n";
        } else {
            json << "\"status\":\"unvalidated_board_candidate\",\"corners_px\":[";
            for (int i=0; i<4; ++i) {
                const auto p = detected->corners[i];
                if (i) json << ',';
                json << '[' << p.x << ',' << p.y << ']';
                cv::line(overlay,p,detected->corners[(i+1)%4],cv::Scalar(0,255,0),2);
                cv::putText(overlay,std::to_string(i),p,cv::FONT_HERSHEY_SIMPLEX,.7,cv::Scalar(0,0,255),2);
            }
            json << "],\"homography\":[";
            for (int r=0;r<3;++r) {
                if (r) json << ',';
                json << '[' << H.at<double>(r,0) << ',' << H.at<double>(r,1) << ',' << H.at<double>(r,2) << ']';
            }
            auto rectified = ac::Homography().warp(frame,H);
            std::array<std::array<cv::Mat,8>,8> cells;
            for(int r=0;r<8;++r) for(int c=0;c<8;++c)
                cells[r][c] = rectified(cv::Rect(c*100,r*100,100,100));
            const auto observed = ac::PieceDetector().analyzeBoard(cells);
            json << "],\"rectified_size\":800,\"cells\":[";
            for(int r=0;r<8;++r) for(int c=0;c<8;++c) {
                const auto state = observed.cells[r][c];
                const char* label = state == ac::CellObservationState::EMPTY ? "empty"
                    : state == ac::CellObservationState::WHITE ? "white" : "black";
                if(r || c) json << ',';
                json << "{\"row\":" << r << ",\"column\":" << c
                     << ",\"square\":null,\"candidate\":\"" << label
                     << "\",\"confidence\":null,\"visibility\":\"unknown\",\"piece_center\":null}";
                cv::rectangle(rectified,cv::Rect(c*100,r*100,100,100),cv::Scalar(0,200,0),1);
                cv::putText(rectified,std::to_string(r)+","+std::to_string(c)+" "+label,
                    cv::Point(c*100+3,r*100+20),cv::FONT_HERSHEY_SIMPLEX,.35,cv::Scalar(0,0,255),1);
            }
            json << "]}\n";
            if (!cv::imwrite((out/"rectified-grid.png").string(),rectified))
                throw std::runtime_error("Could not save rectified image");
        }
        if (!cv::imwrite((out/"corners.png").string(),overlay))
            throw std::runtime_error("Could not save overlay");
        return 0;
    } catch(const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 2;
    }
}
