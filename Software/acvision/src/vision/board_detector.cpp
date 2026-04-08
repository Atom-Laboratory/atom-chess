/**
 * @file board_detector.cpp
 * @brief Implementação do detector de tabuleiro.
 */    
#include "vision/board_detector.hpp"

#include <opencv2/calib3d.hpp>
#include <opencv2/imgproc.hpp>

namespace ac {
/**
 * @brief Detecta o tabuleiro em uma imagem e estima seus quatro cantos externos.
 *
 * O algoritmo atual:
 * 1. Converte a imagem para tons de cinza
 * 2. Detecta os cantos internos do padrão xadrez (7x7)
 * 3. Refina os pontos detectados com precisão subpixel
 * 4. Extrapola os quatro cantos externos do tabuleiro
 *
 * @param frame Frame de entrada capturado pela câmera.
 * @return std::optional<BoardCorners> Cantos detectados ou std::nullopt.
 */
std::optional<BoardCorners> BoardDetector::detect(const cv::Mat& frame) const {
    if (frame.empty()) return std::nullopt;
    
    cv::Mat gray;
    cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);

    cv::Size pattern(7, 7);
    std::vector<cv::Point2f> corners;

    bool found = cv::findChessboardCorners(
        gray,
        pattern,
        corners,
        cv::CALIB_CB_ADAPTIVE_THRESH | cv::CALIB_CB_NORMALIZE_IMAGE
    );

    if (!found) return std::nullopt;

    cv::cornerSubPix(
        gray,
        corners,
        cv::Size(11,11),
        cv::Size(-1,-1),
        cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 30, 0.1)
    );

    cv::Point2f tl_in = corners[0];
    cv::Point2f tr_in = corners[6];
    cv::Point2f bl_in = corners[42];
    cv::Point2f br_in = corners[48];

    cv::Point2f vx = (tr_in - tl_in) / 6.0f;
    cv::Point2f vy = (bl_in - tl_in) / 6.0f;

    cv::Point2f tl = tl_in - 0.5f*vx - 0.5f*vy;
    cv::Point2f tr = tr_in + 0.5f*vx - 0.5f*vy;
    cv::Point2f br = br_in + 0.5f*vx + 0.5f*vy;
    cv::Point2f bl = bl_in - 0.5f*vx + 0.5f*vy;

    return BoardCorners{{tl, tr, br, bl}};
}

}
