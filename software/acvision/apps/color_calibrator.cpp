#include <opencv2/opencv.hpp>
#include <iostream>
#include "piece_detector/piece_detector_config.hpp"
#include "camera/camera.hpp"

using namespace cv;
using namespace std;
using namespace ac;

// Global variables to use with the OpenCV mouse.
Mat current_frame;
Point click_point;
bool clicked = false;

// Function called whenever the user clicks on the screen.
void onMouse(int event, int x, int y, int, void*) {
    if (event == EVENT_LBUTTONDOWN) {
        click_point = Point(x, y);
        clicked = true;
    }
}

// Extracts the exact color of the clicked pixel and creates a safety margin (tolerance).
ColorProfile calculateProfile(const Mat& hsv_image, Point p, int tolerance = 30) {
    Vec3b hsv_pixel = hsv_image.at<Vec3b>(p);
    int h = hsv_pixel[0];
    int s = hsv_pixel[1];
    int v = hsv_pixel[2];

    ColorProfile profile;
    // Hue goes up to 180 in OpenCV. Saturate and Value go up to 255.
    profile.lowerBound = Scalar(max(0, h - tolerance), max(0, s - tolerance), max(0, v - tolerance));
    profile.upperBound = Scalar(min(180, h + tolerance), min(255, s + tolerance), min(255, v + tolerance));
    return profile;
}

int main() {
    
    // Using the initialization required by the acvision library
    ac::Camera cam(
        1,                     // Camera port (0 or 1)
        ac::Resolution::VGA,   // Resolution
        ac::Backend::V4L2      // Backend
    );

    // The function is called is_opened().
    if (!cam.is_opened()) {
        cerr << "Failed to open camera!" << endl;
        return -1;
    }

    PieceDetectorConfig config;
    config.useCalibration = true;

    namedWindow("Calibration", WINDOW_AUTOSIZE);
    setMouseCallback("Calibration", onMouse);

    cout << "--- Piece Color Calibration ---" << endl;
    cout << "1. Place a WHITE piece in front of the camera and click on it." << endl;

    bool white_calibrated = false;
    bool black_calibrated = false;

    while (true) {
        
        // The function is called capture_frame and receives the Matrix by reference.
        if (!cam.capture_frame(current_frame)) {
            cerr << "Failed to capture frame." << endl;
            break;
        }
        
        if (current_frame.empty()) break;

        Mat display_frame = current_frame.clone();

        // Displays instructions on screen.
        if (!white_calibrated) {
            putText(display_frame, "Click on a WHITE piece", Point(10, 30), FONT_HERSHEY_SIMPLEX, 1, Scalar(255, 255, 255), 2);
        } else if (!black_calibrated) {
            putText(display_frame, "Click on a BLACK piece", Point(10, 30), FONT_HERSHEY_SIMPLEX, 1, Scalar(0, 0, 0), 2);
        } else {
            putText(display_frame, "Calibration complete! Press ESC to exit.", Point(10, 30), FONT_HERSHEY_SIMPLEX, 0.8, Scalar(0, 255, 0), 2);
        }

        imshow("Calibration", display_frame);

        // If the user clicked...
        if (clicked) {
            Mat hsv;
            cvtColor(current_frame, hsv, COLOR_BGR2HSV);

            if (!white_calibrated) {
                config.whiteProfile = calculateProfile(hsv, click_point);
                white_calibrated = true;
                cout << "White piece calibrated." << endl;
                cout << "2. Place a BLACK piece in front of the camera and click on it." << endl;
            } else if (!black_calibrated) {
                config.blackProfile = calculateProfile(hsv, click_point);
                black_calibrated = true;
                cout << "Black piece calibrated. Press ESC to exit." << endl;
            }
            clicked = false;
        }

        // Press ESC to close.
        if (waitKey(30) == 27) { 
            break;
        }
    }

    cout << "Calibration finished." << endl;
    return 0;
}