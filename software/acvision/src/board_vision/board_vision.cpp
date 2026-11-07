/**
 * @file board_vision.cpp
 * @brief Chessboard detection and corner estimation for camera calibration.
 */    
#include "board_vision/board_vision.hpp"

#include <opencv2/opencv.hpp>
#include <opencv2/calib3d.hpp>
#include <opencv2/imgproc.hpp>
#include <algorithm>
#include <cmath>
#include <vector>
#include <opencv2/calib3d.hpp>

namespace ac {
    
    /**
    * @brief Detects the chessboard in an image and estimates its four outer corners.
    *
    * The current algorithm:
    * 1. Converts the image to grayscale
    * 2. Detects the internal corners of the chessboard pattern (7x7)
    * 3. Refines the detected points with subpixel accuracy
    * 4. Extrapolates the four outer corners of the chessboard
    *
    * @param frame Input image in which to detect the chessboard.
    * @return std::optional<BoardCorners> Detected corners or std::nullopt.
    */
    std::optional<BoardCorners> BoardDetector::detect(const cv::Mat& frame) const {
        if (frame.empty()) {
            return std::nullopt;
        }

        if (auto result = detectByChessboardPattern(frame)) {
            return result;
        }

        return std::nullopt; // A rectangle alone is not evidence of a chessboard.
    }

    /**
    * @brief Detecta o tabuleiro de xadrez em um frame.
    *
    * @param frame Imagem de entrada.
    * @return std::optional<BoardCorners> Cantos detectados ou std::nullopt.
    */
    std::optional<BoardCorners> BoardDetector::detectByChessboardPattern(const cv::Mat& frame) const {
        cv::Mat gray;
        if (frame.channels() == 3) {
            cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
        } else {
            gray = frame.clone();
        }

        cv::Mat processed;
        cv::equalizeHist(gray, processed);
        cv::GaussianBlur(processed, processed, cv::Size(5, 5), 0);

        cv::Size patternSize(7, 7);
        std::vector<cv::Point2f> innerCorners;

        bool found = false;

        #if CV_VERSION_MAJOR >= 4
            found = cv::findChessboardCornersSB(processed, patternSize, innerCorners);
        #endif

            if (!found) {
                found = cv::findChessboardCorners(
                    processed,
                    patternSize,
                    innerCorners,
                    cv::CALIB_CB_ADAPTIVE_THRESH | cv::CALIB_CB_NORMALIZE_IMAGE
                );
            }

            if (!found) {
                return std::nullopt;
            }

            cv::cornerSubPix(
                gray,
                innerCorners,
                cv::Size(11, 11),
                cv::Size(-1, -1),
                cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 30, 0.1)
            );

            std::vector<cv::Point2f> grid;
            for (int r=1;r<=7;++r) for (int c=1;c<=7;++c)
                grid.emplace_back(static_cast<float>(c),static_cast<float>(r));
            const auto gridToImage = cv::findHomography(grid,innerCorners,0);
            if (gridToImage.empty() || !cv::checkRange(gridToImage)) return std::nullopt;
            std::vector<cv::Point2f> outer;
            cv::perspectiveTransform(std::vector<cv::Point2f>{{0,0},{8,0},{8,8},{0,8}},outer,gridToImage);
            if (!cv::isContourConvex(outer)) return std::nullopt;
            for (const auto& p : outer)
                if (!std::isfinite(p.x) || !std::isfinite(p.y) || p.x<0 || p.y<0 ||
                    p.x>=frame.cols || p.y>=frame.rows) return std::nullopt;
            // Rotate the ordered perimeter to its image top-left. Chess orientation
            // remains unknown; never choose corners independently (duplicate risk).
            if (cv::contourArea(outer,true)<0) std::reverse(outer.begin(),outer.end());
            const auto first=std::min_element(outer.begin(),outer.end(),[](const auto& a,const auto& b){
                return a.x+a.y < b.x+b.y;
            });
            std::rotate(outer.begin(),first,outer.end());
            return BoardCorners{{outer[0],outer[1],outer[2],outer[3]}};
    }

    /**
    * @brief Rezises Image to a perfect square.
    * @param 
    * @param 
    * @return
    */
    cv::Mat normalizeImage(const cv::Mat& topDownImage, int fixedSize) {
        cv::Mat normalizedImage;
        cv::resize(topDownImage, normalizedImage, cv::Size(fixedSize, fixedSize));
        return normalizedImage;
    }

    /**
    * @brief Partitions the ChessBoard image in 64 squares.
    *
    * @param 
    * @param 
    * @return
    */
    void partitionBoard(const cv::Mat& normalizedImage, cv::Mat board[8][8]) {
        int squareSize = normalizedImage.cols / 8;

        for (int r = 0; r < 8; ++r) {
            for (int c = 0; c < 8; ++c) {
                int x = c * squareSize;
                int y = r * squareSize;
                
                cv::Rect roi(x, y, squareSize, squareSize);
                
                board[r][c] = normalizedImage(roi);
            }
        }
    }

} 
