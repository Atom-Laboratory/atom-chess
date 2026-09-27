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

std::string FenGenerator::serializePiecePlacement(const Board& board)
{
    std::string fen;

    for (int row = 0; row < 8; ++row) {
        int emptySquares = 0;

        for (int column = 0; column < 8; ++column) {
            const Piece piece = board.pieceAt({row, column});
            if (piece.type == PieceType::None) {
                ++emptySquares;
                continue;
            }

            if (emptySquares > 0) {
                fen += std::to_string(emptySquares);
                emptySquares = 0;
            }

            fen += pieceToChar(piece);
        }

        if (emptySquares > 0) {
            fen += std::to_string(emptySquares);
        }

        if (row < 7) {
            fen += '/';
        }
    }

    return fen;
}

std::string FenGenerator::serializeCastlingRights(const Board& board)
{
    const CastlingRights& rights = board.castlingRights();
    std::string field;

    if (rights.whiteKingSide) field += 'K';
    if (rights.whiteQueenSide) field += 'Q';
    if (rights.blackKingSide) field += 'k';
    if (rights.blackQueenSide) field += 'q';

    return field.empty() ? "-" : field;
}

} // namespace ac::chess
