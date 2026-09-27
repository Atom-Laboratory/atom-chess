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
    std::string fen = serializePiecePlacement(board);
    fen += ' ';
    fen += board.sideToMove() == PieceColor::White ? 'w' : 'b';
    fen += ' ';
    fen += serializeCastlingRights(board);
    fen += ' ';
    fen += serializeEnPassant(board);
    fen += ' ';
    fen += std::to_string(board.halfmoveClock());
    fen += ' ';
    fen += std::to_string(board.fullmoveNumber());
    return fen;
}

} // namespace ac::chess
