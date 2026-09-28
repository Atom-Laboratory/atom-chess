#ifndef AC_FEN_GENERATOR_HPP
#define AC_FEN_GENERATOR_HPP

#include <string>

#include "board/board.hpp"

namespace ac::chess {

/**
 * @class FenGenerator
 * @brief Serializes the authoritative Board state into Forsyth-Edwards Notation.
 *
 * FenGenerator consumes only Chess Core state. It has no dependency on
 * Computer Vision, Motion Planning, or external engine state.
 *
 * The generated string contains all six standard FEN fields:
 * 1. piece placement;
 * 2. side to move;
 * 3. castling availability;
 * 4. en-passant target square;
 * 5. halfmove clock;
 * 6. fullmove number.
 */
class FenGenerator
{
public:
    /**
     * @brief Generates a complete six-field FEN string.
     * @param board Authoritative Board state to serialize.
     * @return Standard FEN representation suitable for UCI engines such as Stockfish.
     */
    static std::string generate(const Board& board);

private:
    /**
     * @brief Serializes only the 8x8 piece-placement field.
     * @param board Board whose piece placement will be encoded.
     * @return Piece-placement field with empty-square compression by rank.
     */
    static std::string serializePiecePlacement(const Board& board);

    /**
     * @brief Serializes current castling rights in canonical KQkq order.
     * @param board Board containing current castling metadata.
     * @return KQkq subset, or "-" when no castling right remains.
     */
    static std::string serializeCastlingRights(const Board& board);

    /**
     * @brief Serializes the current en-passant target square.
     * @param board Board containing the optional en-passant target.
     * @return Algebraic square such as "e3", or "-" when unavailable.
     */
    static std::string serializeEnPassant(const Board& board);

    /**
     * @brief Converts a non-empty chess piece to its FEN character.
     * @param piece Concrete chess piece.
     * @return Lowercase character for Black or uppercase character for White.
     */
    static char pieceToChar(Piece piece);
};

} // namespace ac::chess

#endif
