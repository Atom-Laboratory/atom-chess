
#include "piece_detector.hpp"

namespace ac
{

std::array<std::array<CellState,8>,8>
PieceDetector::analyzeBoard(
    const std::array<std::array<cv::Mat,8>,8>& boardCells) const
{
    std::array<std::array<CellState,8>,8> result;

    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            result[r][c] = analyzeCell(boardCells[r][c]);
        }
    }

    return result;
}

CellState PieceDetector::analyzeCell(const cv::Mat& cell) const
{
    if(cell.empty())
        return CellState::EMPTY;

    cv::Mat roi = extractCenterROI(cell);
    double edgeDensity = computeEdgeDensity(roi);

    if(edgeDensity < 0.02)
        return CellState::EMPTY;

    if(isWhitePiece(roi))
        return CellState::WHITE;

    return CellState::BLACK;
}

cv::Mat PieceDetector::extractCenterROI(const cv::Mat& cell) const
{
    int x = cell.cols * 0.25;
    int y = cell.rows * 0.25;
    int w = cell.cols * 0.5;
    int h = cell.rows * 0.5;

    return cell(cv::Rect(x,y,w,h));
}

cv::Mat PieceDetector::normalizeLighting(const cv::Mat& input) const
{
    cv::Mat gray;
    cv::cvtColor(input, gray, cv::COLOR_BGR2GRAY);

    cv::Ptr<cv::CLAHE> clahe = cv::createCLAHE(2.0, cv::Size(8,8));

    cv::Mat normalized;
    clahe->apply(gray, normalized);

    return normalized;
}

double PieceDetector::computeEdgeDensity(const cv::Mat& cell) const
{
    cv::Mat norm = normalizeLighting(cell);

    cv::Mat edges;
    cv::Canny(norm, edges, 50, 150);

    double edgePixels = cv::countNonZero(edges);
    double total = cell.rows * cell.cols;

    return edgePixels / total;
}

bool PieceDetector::isWhitePiece(const cv::Mat& cell) const
{
    cv::Mat norm = normalizeLighting(cell);

    cv::Scalar mean, stddev;
    cv::meanStdDev(norm, mean, stddev);

    return (mean[0] > 130.0 && stddev[0] > 20.0);
}

}
