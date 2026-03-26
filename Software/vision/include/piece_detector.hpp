
#ifndef AC_PIECE_DETECTOR_HPP
#define AC_PIECE_DETECTOR_HPP

#include <opencv2/opencv.hpp>
#include <array>

namespace ac
{

enum class CellState
{
    EMPTY,
    WHITE,
    BLACK
};

class PieceDetector
{
public:
    std::array<std::array<CellState,8>,8> analyzeBoard(
        const std::array<std::array<cv::Mat,8>,8>& boardCells
    ) const;

private:
    CellState analyzeCell(const cv::Mat& cell) const;

    cv::Mat extractCenterROI(const cv::Mat& cell) const;
    cv::Mat normalizeLighting(const cv::Mat& input) const;
    double computeEdgeDensity(const cv::Mat& cell) const;
    bool isWhitePiece(const cv::Mat& cell) const;
};

}

#endif
