#include <gtest/gtest.h>
#include <array>
#include <string>

#include "fen_generator/fen_generator.hpp"
#include "piece_detector/piece_detector.hpp"

using namespace ac;

/**
 * @brief Testa geração básica de FEN
 */
TEST(FenGeneratorTest, GeraFenBasico)
{
    std::array<std::array<CellState, 8>, 8> board{};

    // Inicializa tudo como EMPTY
    for(int r = 0; r < 8; r++)
    {
        for(int c = 0; c < 8; c++)
        {
            board[r][c] = CellState::EMPTY;
        }
    }

    // Adiciona algumas peças
    board[0][0] = CellState::BLACK;
    board[0][1] = CellState::BLACK;
    board[7][6] = CellState::WHITE;
    board[7][7] = CellState::WHITE;

    std::string fen = FenGenerator::generate(board);

    EXPECT_EQ(fen, "pp6/8/8/8/8/8/8/6PP w - - 0 1");
}

/**
 * @brief Testa compressão de casas vazias
 */
TEST(FenGeneratorTest, CompressaoDeEspacos)
{
    std::array<std::array<CellState, 8>, 8> board{};

    // Tudo vazio
    for(auto& row : board)
        for(auto& cell : row)
            cell = CellState::EMPTY;

    std::string fen = FenGenerator::generate(board);

    EXPECT_EQ(fen, "8/8/8/8/8/8/8/8 w - - 0 1");
}