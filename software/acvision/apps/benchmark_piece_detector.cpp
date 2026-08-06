/**
 * @file benchmark_piece_detector.cpp
 * @brief Executable for quantitatively evaluating the accuracy of the PieceDetector.
 */

#include <iostream>
#include <filesystem>
#include <chrono>
#include <string>
#include <vector>


#include <opencv2/opencv.hpp>


// #include "board_vision/board_vision.hpp"
// #include "piece_detector/piece_detector.hpp"
// #include "fen_generator/fen_generator.hpp" 

namespace fs = std::filesystem;

int main(int argc, char** argv) {
    // 1. Dataset Path Configuration
    std::string dataset_path = "../assets/dataset"; // Standard path
    if (argc > 1) {
        dataset_path = argv[1];
    }

    std::cout << "[INFO] Iniciando Benchmark de Detecção de Peças...\n";
    std::cout << "[INFO] Lendo imagens em: " << dataset_path << "\n\n";

    if (!fs::exists(dataset_path) || !fs::is_directory(dataset_path)) {
        std::cerr << "[ERRO] Pasta do dataset nao encontrada. Crie a pasta ou passe o caminho via argumento.\n";
        return -1;
    }

    // 2. Metric Variables (Counters)
    int total_images = 0;
    int board_detected_count = 0;
    int grid_extracted_count = 0;
    
    int total_squares_evaluated = 0;
    int squares_correctly_classified = 0;
    
    int total_pieces_expected = 0;
    int pieces_correctly_detected = 0;
    int pieces_correctly_colored = 0;
    
    int fen_perfect_match_count = 0;
    
    double total_processing_time_ms = 0.0;

    // 3. Image Processing Loop
    for (const auto& entry : fs::directory_iterator(dataset_path)) {
        if (entry.path().extension() == ".png" || entry.path().extension() == ".jpg") {
            total_images++;
            std::string image_path = entry.path().string();
            
            // Start the timer.
            auto start_time = std::chrono::high_resolution_clock::now();

            // ==========================================
            // This is where the future vision pipeline will come in.
            // cv::Mat img = cv::imread(image_path);
            // BoardDetection -> Homography -> PieceDetector -> FEN
            // ==========================================

            // For the stopwatch
            auto end_time = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double, std::milli> duration = end_time - start_time;
            total_processing_time_ms += duration.count();
        }
    }

    // 4. Generation of the Final Report (As per Issue #91)
    std::cout << "========================================\n";
    std::cout << "          RESUMO DO BENCHMARK           \n";
    std::cout << "========================================\n";
    std::cout << "Dataset: " << total_images << " imagens\n\n";

    if (total_images > 0) {
        std::cout << "Board Detection ............. " << (board_detected_count * 100.0 / total_images) << "%\n";
        std::cout << "Grid Extraction ............. " << (grid_extracted_count * 100.0 / total_images) << "%\n\n";
        
        // Avoid division by zero in detailed metrics.
        double sq_accuracy = total_squares_evaluated > 0 ? (squares_correctly_classified * 100.0 / total_squares_evaluated) : 0.0;
        double piece_accuracy = total_pieces_expected > 0 ? (pieces_correctly_detected * 100.0 / total_pieces_expected) : 0.0;
        double color_accuracy = pieces_correctly_detected > 0 ? (pieces_correctly_colored * 100.0 / pieces_correctly_detected) : 0.0;

        std::cout << "Casas corretamente classificadas .... " << sq_accuracy << "%\n";
        std::cout << "Pecas corretamente detectadas ....... " << piece_accuracy << "%\n";
        std::cout << "Cor corretamente identificada ....... " << color_accuracy << "%\n\n";

        std::cout << "FEN identico ao esperado ............ " << fen_perfect_match_count << " / " << total_images 
                  << " (" << (fen_perfect_match_count * 100.0 / total_images) << "%)\n\n";

        std::cout << "Tempo medio por imagem .............. " << (total_processing_time_ms / total_images) << " ms\n";
    } else {
        std::cout << "[AVISO] Nenhuma imagem processada para gerar metricas.\n";
    }
    std::cout << "========================================\n";

    return 0;
}