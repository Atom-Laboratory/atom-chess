#pragma once

#include <string>
#include "board/board.hpp"

namespace ac
{

/**
 * @class FenGenerator
 * @brief Serializes a Board's state into Forsyth-Edwards Notation (FEN).
 *
 * The generator consumes exclusively the state exposed by the Board State
 * module (`Board`). It has no dependency on Computer Vision or Motion
 * Planning, so it can run purely on the logical game state.
 *
 * The produced string contains all six standard FEN fields and is
 * compatible with UCI engines such as Stockfish (see ac::chess::engine::StockfishUCI).
 */
class FenGenerator
{
public:

    /**
     * @brief Generates a full FEN string representing the given board.
     *
     * @param board The current board state.
     * @return std::string A FEN string with piece placement, side to move,
     *         castling availability, en passant target square, halfmove
     *         clock and fullmove number, in that order.
     */
    static std::string generate(const Board& board);

private:

    /// @brief Serializes the 8x8 piece placement field (ranks 8 -> 1).
    static std::string serializePiecePlacement(const Board& board);

    /// @brief Serializes castling availability, e.g. "KQkq" or "-".
    static std::string serializeCastlingRights(const Board& board);

    /// @brief Serializes the en passant target square, e.g. "e3" or "-".
    static std::string serializeEnPassant(const Board& board);

    /// @brief Maps a Piece to its FEN character (uppercase = white).
    static char pieceToChar(const Piece& piece);
};

}
