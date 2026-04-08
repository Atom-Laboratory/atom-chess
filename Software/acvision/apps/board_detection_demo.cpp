/**
 * @file board_detection_demo.cpp
 * @brief Aplicação de demonstração para detecção de tabuleiro em tempo real.
 *
 * Este executável captura frames da câmera e utiliza o módulo BoardDetector
 * para localizar um tabuleiro de xadrez na imagem.
 *
 * Quando o tabuleiro é encontrado, a aplicação desenha:
 * - os quatro cantos estimados do tabuleiro
 * - as linhas do quadrilátero correspondente
 * - uma mensagem indicando sucesso da detecção
 *
 * Esta aplicação é voltada para testes e validação visual da pipeline inicial
 * de visão computacional.
 */
#include "camera/camera.hpp"
#include "vision/board_detector.hpp"

#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>

/**
 * @brief Ponto de entrada da aplicação de demonstração.
 *
 * Inicializa a câmera, captura frames continuamente e tenta detectar o tabuleiro
 * em cada frame capturado.
 *
 * @return int Código de saída da aplicação.
 */
int main() {
    ac::Camera cam(0, 640, 480, ac::Backend::V4L2);

    if (!cam.is_opened()) {
        std::cerr << "Erro ao abrir camera\n";
        return -1;
    }

    ac::BoardDetector detector;

    while (true) {
        auto frame = cam.capture_frame();

        auto result = detector.detect(frame);

        if (result) {
            auto c = result->corners;

            for (auto &p : c) {
                cv::circle(frame, p, 5, {0,0,255}, -1);
            }
            
            cv::line(frame, c[0], c[1], {255,0,0}, 2);
            cv::line(frame, c[1], c[2], {255,0,0}, 2);
            cv::line(frame, c[2], c[3], {255,0,0}, 2);
            cv::line(frame, c[3], c[0], {255,0,0}, 2);

            cv::putText(frame, "Board detected", cv::Point(20, 30),
                        cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(0,255,0), 2);
        } else {
            cv::putText(frame, "Board not detected", cv::Point(20, 30),
                        cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(0,0,255), 2);
        }

        cv::imshow("Board", frame);

        int k = cv::waitKey(1);
        if (k == 27 || k == 'q') break;
    }
}
