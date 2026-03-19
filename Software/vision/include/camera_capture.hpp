#pragma once 

#include <opencv2/opencv.hpp> 

cv::Mat capture_camera_frame(int camera_id = 0);

/////////////////  Exemplo Opcional: Abre a Webcam e captura um frame em streaming caso a tecla "espaço" for precionada //////////////////////

//cv::Mat capture_camera_on_stream(int camera_id = 0);