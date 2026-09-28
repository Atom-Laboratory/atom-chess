#pragma once

#include "board/board.hpp"
#include "board/move.hpp"

namespace ac::chess {

/**
 * @class MoveApplier
 * @brief Applies an already validated move to the authoritative Board state.
 *
 * MoveApplier is the mutation boundary of Chess Core. It does not decide
 * whether a move is legal; that responsibility belongs to MoveValidator.
 *
 * Applying a move updates both piece placement and all FEN metadata that can
 * be derived from the transition:
 * - side to move;
 * - castling rights;
 * - en-passant target;
 * - halfmove clock;
 * - fullmove number.
 *
 * This separation keeps rule validation independent from deterministic state
 * mutation and allows the resulting Board to be serialized directly to FEN.
 */
class MoveApplier {
public:
    /**
     * @brief Applies a validated move and atomically updates Board metadata.
     * @param board Authoritative Board instance to mutate.
     * @param move Previously validated chess move.
     *
     * @pre move.from contains the moving piece.
     * @pre Special-move flags are already validated by MoveValidator or
     *      another trusted caller.
     *
     * @post Piece placement reflects the move.
     * @post FEN metadata reflects the resulting game state.
     */
    static void apply(Board& board, const Move& move);

private:
    /**
     * @brief Relocates the rook portion of an already validated castle.
     * @param board Board being mutated.
     * @param move King move carrying the castle flag.
     *
     * The rook source/target columns are inferred from the king destination.
     */
    static void moveCastlingRook(Board& board, const Move& move);

    /**
     * @brief Removes the pawn captured by an already validated en-passant move.
     * @param board Board being mutated.
     * @param move En-passant move whose destination identifies the captured file.
     */
    static void removeEnPassantPawn(Board& board, const Move& move);
};

} // namespace ac::chess
