#include "board_geometry/board_geometry.hpp"

// Task 1.3: Correção de Perspectiva (Homografia)
cv::Mat corrigirPerspectiva(const cv::Mat& frameOriginal, const std::vector<cv::Point2f>& cantos) {
    if (cantos.size() != 4) {
        return cv::Mat(); // Proteção: retorna matriz vazia se não vierem os 4 cantos
    }

    // Define uma resolução temporária alta para a homografia (1000x1000)
    float tam = 1000.0f; 
    
    // Mapeamento dos pontos de destino para a visão aérea (Top-Down)
    // Ordem: Superior-Esquerdo, Superior-Direito, Inferior-Direito, Inferior-Esquerdo
    std::vector<cv::Point2f> pontosDestino = {
        cv::Point2f(0.0f, 0.0f),
        cv::Point2f(tam, 0.0f),
        cv::Point2f(tam, tam),
        cv::Point2f(0.0f, tam)
    };

    // Calcula a matriz de homografia OpenCV
    cv::Mat H = cv::getPerspectiveTransform(cantos, pontosDestino);

    // Transforma a perspectiva da imagem
    cv::Mat imagemTopDown;
    cv::warpPerspective(frameOriginal, imagemTopDown, H, cv::Size(tam, tam));

    return imagemTopDown;
}

// Task 1.4: Normalização da Imagem
cv::Mat normalizarImagem(const cv::Mat& imagemTopDown, int tamanhoFixo) {
    cv::Mat imagemNormalizada;
    // Força a imagem a ser perfeitamente quadrada para garantir divisões exatas por 8
    cv::resize(imagemTopDown, imagemNormalizada, cv::Size(tamanhoFixo, tamanhoFixo));
    return imagemNormalizada;
}

// Task 1.5: Segmentação do Tabuleiro
void segmentarTabuleiro(const cv::Mat& imagemNormalizada, cv::Mat board[8][8]) {
    // Como a resolução foi normalizada (ex: 800), cada casa terá exatamente tamanhoFixo / 8 (ex: 100)
    int tamanhoCasa = imagemNormalizada.cols / 8;

    for (int linha = 0; linha < 8; ++linha) {
        for (int coluna = 0; coluna < 8; ++coluna) {
            int x = coluna * tamanhoCasa;
            int y = linha * tamanhoCasa;
            
            // Define a Região de Interesse (ROI) para o recorte geométrico
            cv::Rect roi(x, y, tamanhoCasa, tamanhoCasa);
            
            // Recorta o quadrado correspondente e salva na matriz board[linha][coluna]
            board[linha][coluna] = imagemNormalizada(roi);
        }
    }
}