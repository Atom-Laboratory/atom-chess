#include "camera/camera.hpp"
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>
#include <chrono>
#include "piece_detector/piece_detector.hpp"

int main(){

    std::string window_name = "Piece Detection";
    cv::namedWindow(window_name, cv::WINDOW_AUTOSIZE);

    ac::PieceDetector piece_detector;

    std::array<std::array<cv::Mat, 8>, 8> boardCells;
    
    cv::Mat whiteCell = cv::Mat(100, 100, CV_8UC3, cv::Scalar(223, 174, 118)); // light brown
    cv::Mat blackCell = cv::Mat(100, 100, CV_8UC3, cv::Scalar(168, 95, 15)); // dark brown
    
    for(int r = 0; r < 8; r++) {
        for(int c = 0; c < 8; c++) {
            if ((r + c) % 2 == 0){
                boardCells[r][c] = blackCell.clone();
            }
            else{
                boardCells[r][c] = whiteCell.clone();
            }
        }
    }

    
    cv::circle(boardCells[0][0], cv::Point(50,50), 20, cv::Scalar(255,255,255), -1);
    cv::circle(boardCells[0][1], cv::Point(50,50), 20, cv::Scalar(20,20,20), -1);

    while (true) {

        std::array<std::array<ac::CellState, 8>, 8> board = piece_detector.analyzeBoard(boardCells);

        cv::Mat boardImage(800, 800, CV_8UC3);

        for(int r = 0; r < 8; r++) {
            for(int c = 0; c < 8; c++) {
                cv::Rect cellRect(c*100, r*100, 100, 100);
                boardCells[r][c].copyTo(boardImage(cellRect));
            }
        }

        cv::imshow(window_name, boardImage);

        if (cv::waitKey(1) == 27 || cv::waitKey(1) == 113) break; 

        std::cout << "Final Board State:" << std::endl;
        for(int r = 0; r < 8; r++) {
            for(int c = 0; c < 8; c++) {
                char stateChar;
                switch (board[r][c]) {
                    case ac::CellState::EMPTY: stateChar = '.'; break;
                    case ac::CellState::WHITE: stateChar = 'W'; break;
                    case ac::CellState::BLACK: stateChar = 'B'; break;
                }
                std::cout << stateChar << " ";
            }
            std::cout << std::endl;
    }
    }

    

    cv::destroyAllWindows();
    return 0;
}