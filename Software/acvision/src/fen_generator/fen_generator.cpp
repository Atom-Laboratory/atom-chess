#include "fen_generator/fen_generator.hpp"

namespace ac
{

/**
 * @brief Implementação da geração de string FEN.
 */
std::string FenGenerator::generate(
    const std::array<std::array<CellState,8>,8>& board)
{
    std::string fen;

    for(int r = 0; r < 8; r++)
    {
        int empty = 0;

        for(int c = 0; c < 8; c++)
        {
            if(board[r][c] == CellState::EMPTY)
            {
                empty++;
            }
            else
            {
                if(empty > 0)
                {
                    fen += std::to_string(empty);
                    empty = 0;
                }

                fen += (board[r][c] == CellState::WHITE) ? 'P' : 'p';
            }
        }

        if(empty > 0)
            fen += std::to_string(empty);

        if(r < 7)
            fen += "/";
    }

    // Campos adicionais do FEN (fixos)
    fen += " w - - 0 1";

    return fen;
}

}