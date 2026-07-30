#include <gtest/gtest.h>
#include "board/board.hpp"
#include "board/piece.hpp"

using namespace ac::chess;

// =========================================================================
// Construction and Clear Tests
// =========================================================================

/**
 * @brief Verifies if the default constructor initializes the board,
 *        and if the clear() method properly empties all 64 squares.
 */
TEST(BoardTest, ConstructionAndClear) {
    Board board;

    // The default constructor calls reset(), so the board MUST NOT be empty.
    // Square (0,0) usually holds a starting Rook, so it shouldn't be empty.
    EXPECT_FALSE(board.isSqrEmpty({0, 0})); 

    // Clear the board
    board.clear();

    // Verify if ALL 64 squares are empty after clear()
    for (std::uint8_t r = 0; r < 8; ++r) {
        for (std::uint8_t c = 0; c < 8; ++c) {
            EXPECT_TRUE(board.isSqrEmpty({r, c}));
        }
    }
}

// =========================================================================
// Update (setPiece) and Query (pieceAt / isSqrEmpty) Tests
// =========================================================================

/**
 * @brief Verifies the insertion, replacement, and removal of pieces on specific squares,
 *        ensuring that other squares are not accidentally affected.
 */
TEST(BoardTest, UpdateAndQueryPieces) {
    Board board;
    board.clear(); // Ensure we start with a 100% empty board for this test

    Square sq{4, 4}; // Center square for testing
    Piece knight{PieceType::Knight, PieceColor::White};

    // 1. Insertion
    board.setPiece(sq, knight);
    EXPECT_FALSE(board.isSqrEmpty(sq));
    
    Piece retrieved = board.pieceAt(sq);
    EXPECT_EQ(retrieved.type, PieceType::Knight);
    EXPECT_EQ(retrieved.color, PieceColor::White);

    // Ensure a piece was not inserted in the wrong square accidentally
    EXPECT_TRUE(board.isSqrEmpty({0, 0}));

    // 2. Replacement
    Piece queen{PieceType::Queen, PieceColor::Black};
    board.setPiece(sq, queen);
    
    retrieved = board.pieceAt(sq);
    EXPECT_EQ(retrieved.type, PieceType::Queen);
    EXPECT_EQ(retrieved.color, PieceColor::Black);

    // 3. Removal (simulated by placing an empty piece)
    board.setPiece(sq, Piece{}); 
    EXPECT_TRUE(board.isSqrEmpty(sq));
}

// =========================================================================
// Comparison Tests (== and != Operators)
// =========================================================================

/**
 * @brief Verifies if the comparison logic between two boards works properly.
 *        Boards with the same pieces in the same positions must be equal.
 */
TEST(BoardTest, CompareBoards) {
    Board board1;
    Board board2;

    // Two freshly created boards should be identical (default starting position)
    EXPECT_TRUE(board1 == board2);
    EXPECT_FALSE(board1 != board2);

    // Altering a single square should make them different
    board1.setPiece({4, 4}, Piece{PieceType::Pawn, PieceColor::White});
    EXPECT_TRUE(board1 != board2);
    EXPECT_FALSE(board1 == board2);

    // Applying the same alteration to the second board should make them equal again
    board2.setPiece({4, 4}, Piece{PieceType::Pawn, PieceColor::White});
    EXPECT_TRUE(board1 == board2);
}