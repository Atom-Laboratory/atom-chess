#include "fen_generator/fen_generator.hpp"
#include <cctype> // Required to use std::toupper

namespace ac::chess {

/**
 * @brief Implementation of FEN string generation.
 */
std::string FenGenerator::generate(const Board& board)
{
    std::string fen;

    for(int r = 0; r < 8; r++)
    {
        int empty = 0;

        for(int c = 0; c < 8; c++)
        {
            Square currentSq{r, c};
            if(board.isSqrEmpty(currentSq))
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

                Piece p = board.pieceAt(currentSq);
                char pieceChar = '?';
                
                // Maps the part type to the standard FEN (lowercase) font.
                switch(p.type) {
                    case PieceType::Pawn:   pieceChar = 'p'; break;
                    case PieceType::Knight: pieceChar = 'n'; break;
                    case PieceType::Bishop: pieceChar = 'b'; break;
                    case PieceType::Rook:   pieceChar = 'r'; break;
                    case PieceType::Queen:  pieceChar = 'q'; break;
                    case PieceType::King:   pieceChar = 'k'; break;
                }
                
                // If the part is white, the letter in FEN should be uppercase.
                if (p.color == PieceColor::White) {
                    pieceChar = std::toupper(pieceChar);
                }
                
                fen += pieceChar;
            }
        }

        if(empty > 0)
            fen += std::to_string(empty);

        if(r < 7)
            fen += "/";
    }

    // Additional FEN fields (fixed)
    fen += " w - - 0 1";

    return fen;
}

}