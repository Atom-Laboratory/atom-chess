#include <vector>
#pragma once

namespace ac {

/**
 * @brief Represents the color of a chess piece.
 */
enum class PieceColor {
    White,
    Black,
    None
};

/**
 * @brief Represents the type of a chess piece.
 */
enum class PieceType {
    Pawn,
    Knight,
    Bishop,
    Rook,
    Queen,
    King,
    None
};

/**
 * @brief Represents a single square on the chessboard containing a piece (or empty).
 */
struct Piece {
    PieceType type{PieceType::None};
    PieceColor color{PieceColor::None};
};

/**
 * @brief Represents a change detected between two board states.
 */
struct BoardChange {
    Piece piece;        // The piece that was moved/captured
    int from_row{-1};   // Starting row index (-1 if unknown/placed)
    int from_col{-1};   // Starting col index (-1 if unknown/placed)
    int to_row{-1};     // Ending row index (-1 if removed)
    int to_col{-1};     // Ending col index (-1 if removed)
};

/**
 * @brief Manages the 8x8 logical representation of the chessboard.
 */
class BoardState {
public:
    /**
     * @brief Constructs an empty board state, initializing all squares to None.
     */
    BoardState();

    /**
     * @brief Default destructor.
     */
    ~BoardState() = default;

    /**
     * @brief Retrieves the piece at a specific row and column.
     * 
     * @param row The row index (0-7).
     * @param col The column index (0-7).
     * @return Piece The piece located at the specified coordinates.
     */
    Piece get_piece(int row, int col) const;

    /**
     * @brief Sets a piece at a specific row and column.
     * 
     * @param row The row index (0-7).
     * @param col The column index (0-7).
     * @param piece The piece object to place on the board.
     */
    void set_piece(int row, int col, const Piece& piece);

    /**
     * @brief Compares this board state with a new one to find differences.
     * * @param new_state The updated board state detected by the camera.
     * @return std::vector<BoardChange> A list of detected changes.
     */
    std::vector<BoardChange> compare_with(const BoardState& new_state) const;
private:
    /**
     * @brief 8x8 matrix representing the 64 squares of the chessboard.
     */
    Piece m_board[8][8];
};

} // namespace ac