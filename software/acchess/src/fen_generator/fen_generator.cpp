#include "fen_generator/fen_generator.hpp"

#include <cctype>

namespace ac
{

std::string FenGenerator::generate(const Board& board)
{
    std::string fen;

    fen += serializePiecePlacement(board);
    fen += ' ';
    fen += (board.sideToMove() == PieceColor::White) ? 'w' : 'b';
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

    for (int r = 0; r < 8; r++)
    {
        int empty = 0;

        for (int c = 0; c < 8; c++)
        {
            Piece piece = board.pieceAt({r, c});

            if (piece.type == PieceType::None)
            {
                empty++;
                continue;
            }

            if (empty > 0)
            {
                fen += std::to_string(empty);
                empty = 0;
            }

            fen += pieceToChar(piece);
        }

        if (empty > 0)
            fen += std::to_string(empty);

        if (r < 7)
            fen += '/';
    }

    return fen;
}

std::string FenGenerator::serializeCastlingRights(const Board& board)
{
    const CastlingRights& rights = board.castlingRights();

    std::string fen;

    if (rights.whiteKingSide)  fen += 'K';
    if (rights.whiteQueenSide) fen += 'Q';
    if (rights.blackKingSide)  fen += 'k';
    if (rights.blackQueenSide) fen += 'q';

    return fen.empty() ? "-" : fen;
}

std::string FenGenerator::serializeEnPassant(const Board& board)
{
    std::optional<Square> target = board.enPassantTarget();

    if (!target.has_value())
        return "-";

    char file = static_cast<char>('a' + target->col);
    char rank = static_cast<char>('8' - target->row);

    return std::string{file, rank};
}

char FenGenerator::pieceToChar(const Piece& piece)
{
    char c;

    switch (piece.type)
    {
        case PieceType::Pawn:   c = 'p'; break;
        case PieceType::Knight: c = 'n'; break;
        case PieceType::Bishop: c = 'b'; break;
        case PieceType::Rook:   c = 'r'; break;
        case PieceType::Queen:  c = 'q'; break;
        case PieceType::King:   c = 'k'; break;
        default:                c = '?'; break;
    }

    return (piece.color == PieceColor::White)
        ? static_cast<char>(std::toupper(static_cast<unsigned char>(c)))
        : c;
}

}
