#ifndef AC_PIECE_DETECTOR_HPP
#define AC_PIECE_DETECTOR_HPP

#include <opencv2/opencv.hpp>
#include <array>

#include "board_observation/board_observation.hpp"

namespace ac
{

/**
 * @class PieceDetector
 * @brief Performs image analysis to detect chess pieces.
 *
 * This class implements a heuristic computer vision pipeline to determine
 * whether a cell is empty or contains a piece, and to identify the piece's color.
 */
class PieceDetector
{
public:

    /**
     * @brief Analyzes all board cells.
     * 
     * @param boardCells 8x8 matrix containing images (cv::Mat) of the cells.
     * @return BoardObservation containing the visual observation of each cell.
     */
    BoardObservation analyzeBoard(
        const std::array<std::array<cv::Mat, 8>, 8>& boardCells
    ) const;

private:

    /**
     * @brief Analyzes a single board cell.
     * 
     * @param cell Image of the cell.
     * @return CellObservationState Detected state of the cell.
     */
    CellObservationState analyzeCell(const cv::Mat& cell) const;

    /**
     * @brief Extracts the central region of the cell image.
     * 
     * Reduces interference from board edges and grid lines.
     * 
     * @param cell Image of the cell.
     * @return cv::Mat Central region of the cell.
     */
    cv::Mat extractCenterROI(const cv::Mat& cell) const;

    /**
     * @brief Normalizes lighting using CLAHE.
     * 
     * @param input Input image.
     * @return cv::Mat Image with normalized lighting.
     */
    cv::Mat normalizeLighting(const cv::Mat& input) const;

    /**
     * @brief Computes edge density using Canny.
     * 
     * @param cell Image of the cell.
     * @return double Ratio of edge pixels to total pixels in the image.
     */
    double computeEdgeDensity(const cv::Mat& cell) const;

    /**
     * @brief Determines if the piece is white based on intensity.
     * 
     * @param roi Image of the region of interest.
     * @return true if it is a white piece, false if it is black.
     */
    bool isWhitePiece(const cv::Mat& roi) const;
};

}

#endif