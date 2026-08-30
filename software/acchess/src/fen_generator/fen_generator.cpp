#include "fen_generator/fen_generator.hpp"

#include <cctype>

namespace ac::chess {
namespace {

char pieceSymbol(Piece piece)
{
    char symbol = '?';

    switch (piece.type) {
        case PieceType::None:   break;
        case PieceType::Pawn:   symbol = 'p'; break;
        case PieceType::Knight: symbol = 'n'; break;
        case PieceType::Bishop: symbol = 'b'; break;
        case PieceType::Rook:   symbol = 'r'; break;
        case PieceType::Queen:  symbol = 'q'; break;
        case PieceType::King:   symbol = 'k'; break;
    }

    if (piece.color == PieceColor::White) {
        symbol = static_cast<char>(std::toupper(
            static_cast<unsigned char>(symbol)
        ));
    }

    return symbol;
}

} // namespace

std::string FenGenerator::generate(const Board& board)
{
    std::string fen;

    for (int row = 0; row < 8; ++row) {
        int emptySquares = 0;

        for (int column = 0; column < 8; ++column) {
            const Square square{row, column};
            if (board.isSqrEmpty(square)) {
                ++emptySquares;
                continue;
            }

            if (emptySquares > 0) {
                fen += std::to_string(emptySquares);
                emptySquares = 0;
            }

            fen += pieceSymbol(board.pieceAt(square));
        }

        if (emptySquares > 0) {
            fen += std::to_string(emptySquares);
        }

        if (row < 7) {
            fen += '/';
        }
    }

    fen += " w - - 0 1";
    return fen;
}

} // namespace ac::chess
