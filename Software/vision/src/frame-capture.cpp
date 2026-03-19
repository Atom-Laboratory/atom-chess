#include <opencv2/imgcodecs.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>

using namespace cv;
using namespace std;


/////////////////  Função que retorna captura da câmera /////////////////

cv::Mat capture_camera_frame(int camera_id = 0) {
    cv::VideoCapture cap(camera_id, cv::CAP_DSHOW);
    cv::Mat frame;

    cap.read(frame); 
    return frame;
}


/////////////////  Exemplo Opcional: Abre a Webcam e captura um frame em streaming caso a tecla "espaço" for precionada //////////////////////


//int capture_camera_on_stream() {
//
//	VideoCapture cap(0, CAP_DSHOW);
//	Mat img;
//
//	while (true) {
//
//		cap.read(img);
//
//		imshow("streaming", img);
//
//		char key = (char)waitKey(1);
//
//		if (key == 32) {
//			int frame = imshow("frame capturado", img);
//		}
//		
//		return frame;
//
//		waitKey(1);
//	}
//}