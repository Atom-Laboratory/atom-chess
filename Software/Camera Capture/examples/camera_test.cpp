#include <iostream>
#include <opencv2/opencv.hpp>
#include "include/camera_capture.hpp" 

int main() {
    cv::Mat frame = capture_camera_frame(0);

    cv::imshow("Frame capturado", frame);
    std::cout << "Pressione qualquer tecla para fechar..." << std::endl;
    cv::waitKey(0);

    return 0;
}



/////////////////  Exemplo Opcional: Abre a Webcam e captura um frame em streaming caso a tecla "espaço" for precionada //////////////////////

//int main() {
//    cv::Mat frame = capture_camera_on_stream(0);
//
//    cv::imshow("Frame capturado", frame);
//    std::cout << "Pressione qualquer tecla para fechar..." << std::endl;
//    cv::waitKey(0);
//
//    return 0;
//}
