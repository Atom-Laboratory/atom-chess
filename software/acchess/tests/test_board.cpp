#include <gtest/gtest.h>
#include "board/board.hpp"
#include "board/piece.hpp"
#include "fen_generator/fen_generator.hpp"

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

// =========================================================================
// Integration Tests (Issue #94)
// =========================================================================

/**
 * @brief Integration test simulating a sequence of board state changes.
 *        Verifies the complex interaction between Board, Piece, and Square
 *        across multiple sequential updates, simulating a basic movement
 *        and a capture scenario to ensure state consistency.
 */
TEST(BoardIntegrationTest, SimulateMoveAndCaptureSequence) {
    Board board;
    board.clear();

    Square sourceSq{1, 4};      // e2 (White Pawn starting position)
    Square targetSq{3, 4};      // e4 (Target empty square)
    Square enemySq{3, 3};       // d4 (Black Pawn position)

    Piece whitePawn{PieceType::Pawn, PieceColor::White};
    Piece blackPawn{PieceType::Pawn, PieceColor::Black};

    // 1. Initial Setup: Place White pawn on e2 and Black pawn on d4
    board.setPiece(sourceSq, whitePawn);
    board.setPiece(enemySq, blackPawn);

    // 2. Simulate Movement: White pawn moves from e2 to e4
    board.setPiece(targetSq, board.pieceAt(sourceSq));
    board.setPiece(sourceSq, Piece{}); // Clear the source square

    EXPECT_TRUE(board.isSqrEmpty(sourceSq));
    EXPECT_FALSE(board.isSqrEmpty(targetSq));
    EXPECT_EQ(board.pieceAt(targetSq).color, PieceColor::White);

    // 3. Simulate Capture: White pawn on e4 captures Black pawn on d4
    board.setPiece(enemySq, board.pieceAt(targetSq));
    board.setPiece(targetSq, Piece{}); // Clear the target square

    EXPECT_TRUE(board.isSqrEmpty(targetSq));
    EXPECT_FALSE(board.isSqrEmpty(enemySq));
    
    // Verify the square now belongs to the White pawn, and Black pawn is gone
    Piece capturedSqPiece = board.pieceAt(enemySq);
    EXPECT_EQ(capturedSqPiece.type, PieceType::Pawn);
    EXPECT_EQ(capturedSqPiece.color, PieceColor::White);
}

/**
 * @brief Integration test verifying the interaction between Board and FEN Generator.
 *        Ensures the board's internal default state is correctly parsed into a FEN string.
 */
TEST(BoardIntegrationTest, FENGeneratorIntegration) {
    Board board;
    
    // The default constructor initializes the board to the standard starting position.
    // Replace "FenGenerator::generate" with the actual class/namespace and method name you use!
    std::string fen = FenGenerator::generate(board); 
    
    // Verify if the generated string is not empty and contains the standard start position signature
    EXPECT_FALSE(fen.empty());
    EXPECT_NE(fen.find("rnbqkbnr/pppppppp"), std::string::npos);
    EXPECT_NE(fen.find("PPPPPPPP/RNBQKBNR"), std::string::npos);
}