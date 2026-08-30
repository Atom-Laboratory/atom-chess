/**
 * @file benchmark_piece_detector.cpp
 * @brief Executable for quantitatively evaluating the accuracy of the PieceDetector.
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <filesystem>
#include <chrono>
#include <string>
#include <vector>

#include <opencv2/opencv.hpp>

// #include "board_vision/board_vision.hpp"
// #include "piece_detector/piece_detector.hpp"
// #include "fen_generator/fen_generator.hpp" 

namespace fs = std::filesystem;

// Function to read the gabarito.txt
std::vector<std::pair<std::string, std::string>> loadGroundTruth(const std::string& filePath) {
    std::vector<std::pair<std::string, std::string>> groundTruth;
    std::ifstream file(filePath);
    std::string line;

    if (!file.is_open()) {
        std::cerr << "[ERRO] Nao foi possivel abrir o arquivo de gabarito: " << filePath << std::endl;
        return groundTruth;
    }

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string imageName;
        std::string fen;

        // Read the image name and FEN, separated by a comma.
        if (std::getline(ss, imageName, ',') && std::getline(ss, fen)) {
            // Remove any whitespace before FEN.
            fen.erase(0, fen.find_first_not_of(" \t"));
            
            // Take only the first part of FEN (before the first space).
            std::string cleanFen = fen.substr(0, fen.find(" "));
            
            groundTruth.push_back({imageName, cleanFen});
        }
    }
    return groundTruth;
}

int main(int argc, char** argv) {
    // 1. Dataset Path Configuration
    // Relative path considering that the executable runs from the build/ folder.
    std::string dataset_path = "software/acvision/tests/dataset"; 
    if (argc > 1) {
        dataset_path = argv[1];
    }

    std::cout << "[INFO] Iniciando Benchmark de Deteccao de Pecas...\n";
    std::cout << "[INFO] Lendo imagens e gabarito em: " << dataset_path << "\n\n";

    if (!fs::exists(dataset_path) || !fs::is_directory(dataset_path)) {
        std::cerr << "[ERRO] Pasta do dataset nao encontrada. Verifique se o caminho esta correto.\n";
        return -1;
    }

    std::string groundTruthPath = dataset_path + "/gabarito.txt";
    auto groundTruth = loadGroundTruth(groundTruthPath);

    if (groundTruth.empty()) {
        std::cerr << "[ERRO] O gabarito.txt esta vazio ou nao foi lido corretamente.\n";
        return -1;
    }

    // 2. Metric Variables (Counters)
    int total_images = 0;
    int board_detected_count = 0; // Practice tests for now.
    int grid_extracted_count = 0;
    
    int total_squares_evaluated = 0;
    int squares_correctly_classified = 0;
    
    int total_pieces_expected = 0;
    int pieces_correctly_detected = 0;
    int pieces_correctly_colored = 0;
    
    int fen_perfect_match_count = 0;
    
    double total_processing_time_ms = 0.0;

    // 3. Processing Loop (Now based on the template)
    for (const auto& entry : groundTruth) {
        total_images++;
        std::string imageName = entry.first;
        std::string expectedFen = entry.second;
        std::string imagePath = dataset_path + "/" + imageName;

        auto start_time = std::chrono::high_resolution_clock::now();

        // ==========================================
        // COMPUTER VISION SIMULATION
        // cv::Mat img = cv::imread(imagePath);
        // BoardDetection -> Homography -> PieceDetector -> FEN
        // ==========================================
        
        // Detection simulation to see the metric in action.
        // FEN of image 01 fixed to test the comparator.
        std::string detectedFen = "2b1kbnr/1pp2pp1/B1q1p3/p1Q4p/P3N2P/5N1R/PPPPPP2/R1B1K3"; 

        auto end_time = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double, std::milli> duration = end_time - start_time;
        total_processing_time_ms += duration.count();

        // FEN check
        std::cout << "Testando: " << imageName << "\n";
        std::cout << "  Esperado:  " << expectedFen << "\n";
        std::cout << "  Detectado: " << detectedFen << "\n";

        if (expectedFen == detectedFen) {
            std::cout << "  -> [PASSOU] FENs conferem!\n";
            fen_perfect_match_count++;
        } else {
            std::cout << "  -> [FALHOU] Diferenca encontrada.\n";
        }
        std::cout << "---------------------------------\n";
    }

    // 4. Generation of the Final Report
    std::cout << "========================================\n";
    std::cout << "           RESUMO DO BENCHMARK          \n";
    std::cout << "========================================\n";
    std::cout << "Dataset: " << total_images << " imagens\n\n";

    if (total_images > 0) {
        std::cout << "Board Detection ............. " << (board_detected_count * 100.0 / total_images) << "%\n";
        std::cout << "Grid Extraction ............. " << (grid_extracted_count * 100.0 / total_images) << "%\n\n";
        
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