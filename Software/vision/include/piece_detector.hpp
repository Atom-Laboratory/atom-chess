#ifndef AC_PIECE_DETECTOR_HPP
#define AC_PIECE_DETECTOR_HPP

#include <opencv2/opencv.hpp>
#include <array>

namespace ac
{

/**
 * @enum CellState
 * @brief Representa o estado de uma célula do tabuleiro.
 */
enum class CellState
{
    EMPTY,  /**< Casa vazia */
    WHITE,  /**< Peça branca */
    BLACK   /**< Peça preta */
};

/**
 * @class PieceDetector
 * @brief Realiza a análise de imagens de células para detectar peças.
 *
 * Esta classe implementa um pipeline de visão computacional baseado em
 * heurísticas para determinar se uma célula está vazia ou contém uma peça,
 * além de identificar a cor da peça.
 */
class PieceDetector
{
public:

    /**
     * @brief Analisa todas as células do tabuleiro.
     *
     * @param boardCells Matriz 8x8 contendo imagens (cv::Mat) das células.
     * @return Matriz 8x8 contendo o estado de cada célula.
     */
    std::array<std::array<CellState,8>,8> analyzeBoard(
        const std::array<std::array<cv::Mat,8>,8>& boardCells
    ) const;

private:

    /**
     * @brief Analisa uma única célula do tabuleiro.
     *
     * @param cell Imagem da célula.
     * @return CellState Estado identificado da célula.
     */
    CellState analyzeCell(const cv::Mat& cell) const;

    /**
     * @brief Extrai a região central da célula.
     *
     * Reduz a interferência de bordas e linhas do tabuleiro.
     *
     * @param cell Imagem original da célula.
     * @return cv::Mat Região central da imagem.
     */
    cv::Mat extractCenterROI(const cv::Mat& cell) const;

    /**
     * @brief Normaliza a iluminação da imagem.
     *
     * Utiliza CLAHE para melhorar contraste e reduzir variações de iluminação.
     *
     * @param input Imagem de entrada.
     * @return cv::Mat Imagem normalizada.
     */
    cv::Mat normalizeLighting(const cv::Mat& input) const;

    /**
     * @brief Calcula a densidade de bordas na imagem.
     *
     * Utilizado para detectar a presença de peças.
     *
     * @param cell Imagem da célula.
     * @return double Proporção de pixels de borda.
     */
    double computeEdgeDensity(const cv::Mat& cell) const;

    /**
     * @brief Determina se a peça presente é branca.
     *
     * Baseado em análise de brilho médio e variação de intensidade.
     *
     * @param cell Imagem da célula.
     * @return true Se a peça for branca.
     * @return false Caso contrário (preta).
     */
    bool isWhitePiece(const cv::Mat& cell) const;
};

}

#endif