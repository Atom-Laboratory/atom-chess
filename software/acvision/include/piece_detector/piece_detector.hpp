#ifndef AC_PIECE_DETECTOR_HPP
#define AC_PIECE_DETECTOR_HPP

#include <opencv2/opencv.hpp>
#include <array>

#include "board_state/board_state.hpp"

namespace ac
{

/**
 * @class PieceDetector
 * @brief Performs image analysis to detect chess pieces.
 *
 * This class implements a heuristic computer vision pipeline to determine
 * whether a cell is empty or contains a piece, and to identify the piece color.
 */
class PieceDetector
{
public:

    /**
     * @brief Analyzes all board cells.
     *
     * @param boardCells 8x8 matrix containing images (cv::Mat) of the cells.
     * @return BoardState containing the visual state of each cell.
     */
    BoardState analyzeBoard(
        const std::array<std::array<cv::Mat, 8>, 8>& boardCells
    ) const;

private:

    /**
     * @brief Analyzes a single board cell.
     *
     * @param cell Image of the cell.
     * @return CellState Detected state of the cell.
     */
    CellState analyzeCell(const cv::Mat& cell) const;

    /**
     * @brief Extracts the central region of the cell image.
     *
     * Reduces interference from board edges and grid lines.
     *
     * @param cell Original cell image.
     * @return cv::Mat Central region of the image.
     */
    cv::Mat extractCenterROI(const cv::Mat& cell) const;

    /**
     * @brief Normalizes lighting in the image.
     *
     * Uses CLAHE to improve contrast and reduce illumination variations.
     *
     * @param input Input image.
     * @return cv::Mat Normalized image.
     */
    cv::Mat normalizeLighting(const cv::Mat& input) const;

    /**
     * @brief Computes the edge density of the image.
     *
     * Used to detect the presence of a piece.
     *
     * @param cell Cell image.
     * @return double Proportion of edge pixels.
     */
    double computeEdgeDensity(const cv::Mat& cell) const;

    /**
     * @brief Determines whether the detected piece is white.
     *
     * Based on mean brightness and intensity variation analysis.
     *
     * @param cell Cell image.
     * @return true if the piece is white.
     * @return false otherwise (black piece).
     */
    bool isWhitePiece(const cv::Mat& cell) const;
};

}

#endif