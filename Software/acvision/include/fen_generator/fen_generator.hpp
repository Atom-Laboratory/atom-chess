#ifndef AC_FEN_GENERATOR_HPP
#define AC_FEN_GENERATOR_HPP

#include <array>
#include <string>
#include "piece_detector/piece_detector.hpp"

namespace ac
{

/**
 * @class FenGenerator
 * @brief Responsável por converter o estado do tabuleiro em uma string no formato FEN.
 *
 * A classe fornece um método estático para gerar a representação textual
 * de um tabuleiro de xadrez com base em uma matriz 8x8 de CellState.
 */
class FenGenerator
{
public:

    /**
     * @brief Gera uma string no formato FEN a partir do estado do tabuleiro.
     *
     * @param board Matriz 8x8 contendo o estado de cada célula (EMPTY, WHITE, BLACK).
     * @return std::string String no formato FEN representando o tabuleiro.
     *
     * @note Apenas a ocupação e cor das peças são consideradas.
     * @note Todas as peças são representadas como peões (P/p).
     * @note Campos adicionais do FEN são definidos com valores fixos.
     */
    static std::string generate(
        const std::array<std::array<CellState,8>,8>& board
    );
};

}

#endif