#include "piece_detector/piece_detector.hpp"

namespace ac
{

/**
 * @brief Analyze all board cells.
 */
OccupancyGrid PieceDetector::analyzeBoard(
    const std::array<std::array<cv::Mat,8>,8>& boardCells) const
{
    OccupancyGrid result;

    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            result.cells[r][c] = analyzeCell(boardCells[r][c]);
        }
    }

    return result;
}

/**
 * @brief Analyze a single cell.
 */
CellObservation PieceDetector::analyzeCell(const cv::Mat& cell) const
{

    CellObservation obs;

    if(cell.empty()){
        obs.state = CellState::EMPTY;
        return obs;
    }

    cv::Mat roi = extractCenterROI(cell);
    double edgeDensity = computeEdgeDensity(roi);

    if(edgeDensity < 0.02)
    {
        obs.state = CellState::EMPTY;
    }
    else if(isWhitePiece(roi))
    {
        obs.state = CellState::WHITE;
    }
    else {
        obs.state = CellState::BLACK;
    }

    obs.roi = roi;
    obs.confidence = 1.0f;

    return obs;
}

/**
 * @brief Extract the central region of the image.
 */
cv::Mat PieceDetector::extractCenterROI(const cv::Mat& cell) const
{
    int x = static_cast<int>(cell.cols * 0.25);
    int y = static_cast<int>(cell.rows * 0.25);
    int w = static_cast<int>(cell.cols * 0.5);
    int h = static_cast<int>(cell.rows * 0.5);

    return cell(cv::Rect(x,y,w,h));
}

/**
 * @brief Normalize lighting using CLAHE.
 */
cv::Mat PieceDetector::normalizeLighting(const cv::Mat& input) const
{
    cv::Mat gray;
    cv::cvtColor(input, gray, cv::COLOR_BGR2GRAY);

    cv::Ptr<cv::CLAHE> clahe = cv::createCLAHE(2.0, cv::Size(8,8));

    cv::Mat normalized;
    clahe->apply(gray, normalized);

    return normalized;
}

/**
 * @brief Compute edge density using Canny.
 */
double PieceDetector::computeEdgeDensity(const cv::Mat& cell) const
{
    cv::Mat norm = normalizeLighting(cell);

    cv::Mat edges;
    cv::Canny(norm, edges, 50, 150);

    double edgePixels = cv::countNonZero(edges);
    double total = cell.rows * cell.cols;

    return edgePixels / total;
}

/**
 * @brief Determine if the piece is white.
 */
bool PieceDetector::isWhitePiece(const cv::Mat& cell) const
{
    cv::Mat norm = normalizeLighting(cell);

    cv::Scalar mean, stddev;
    cv::meanStdDev(norm, mean, stddev);

    return (mean[0] > 130.0 && stddev[0] > 20.0);
}

}