#include <opencv2/imgcodecs.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>

using namespace cv;
using namespace std;


/////////////////  Abre a Webcam e captura um frame em streaming caso a tecla "espaço" for precionada //////////////////////

void main() {

	VideoCapture cap(0, CAP_DSHOW);
	Mat img;

	while (true) {

		cap.read(img);

		imshow("streaming", img);

		char key = (char)waitKey(1);

		if (key == 32) { 
			imshow("frame capturado", img);
		}

		waitKey(1);
	}
}


/////////////////  Código sem streaming, caso necessário (Apenas captura um frame da câmera) //////////////////////

//void main() {
//    VideoCapture cap(0, CAP_DSHOW);
//    Mat img;
//
//    cap.read(img);
//    imshow("Frame Capturado", img);
//	waitKey(0);
//}