#include <gtest/gtest.h>
#include <string>

#include "fen_generator/fen_generator.hpp"
#include "board/board.hpp"

using namespace ac;

namespace
{

/// @brief Builds a completely empty board (no pieces, default metadata).
Board emptyBoard()
{
    Board board;
    board.clear();
    return board;
}

}

/**
 * @brief The standard starting position must serialize to the well known
 *        FEN string, including default castling rights and move counters.
 */
TEST(FenGeneratorTest, InitialPosition)
{
    Board board; // Board() calls reset() internally.

    EXPECT_EQ(
        FenGenerator::generate(board),
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    );
}

/**
 * @brief Empty ranks must be compressed into a single digit and mixed
 *        occupancy must fall back to piece letters plus digits.
 */
TEST(FenGeneratorTest, EmptyBoardCompression)
{
    Board board = emptyBoard();

    EXPECT_EQ(
        FenGenerator::generate(board),
        "8/8/8/8/8/8/8/8 w KQkq - 0 1"
    );
}

/**
 * @brief An arbitrary, non-standard position (mid-game-like) must be
 *        serialized with the correct piece letters and empty-square counts.
 */
TEST(FenGeneratorTest, ArbitraryPosition)
{
    Board board = emptyBoard();

    board.setPiece({0, 4}, {PieceType::King, PieceColor::Black});
    board.setPiece({7, 4}, {PieceType::King, PieceColor::White});
    board.setPiece({4, 4}, {PieceType::Pawn, PieceColor::White});
    board.setPiece({3, 3}, {PieceType::Knight, PieceColor::Black});

    board.setSideToMove(PieceColor::Black);
    board.setCastlingRights({false, false, false, false});

    EXPECT_EQ(
        FenGenerator::generate(board),
        "4k3/8/8/3n4/4P3/8/8/4K3 b - - 0 1"
    );
}

/**
 * @brief Promoted pieces are just regular pieces from the Board's point of
 *        view (the promotion itself is handled elsewhere); the generator
 *        must still place them with the correct letter on the back rank.
 */
TEST(FenGeneratorTest, PromotedPieceOnBackRank)
{
    Board board = emptyBoard();

    board.setPiece({0, 4}, {PieceType::King, PieceColor::Black});
    board.setPiece({7, 4}, {PieceType::King, PieceColor::White});
    // A white pawn that has just promoted to a queen on a8.
    board.setPiece({0, 0}, {PieceType::Queen, PieceColor::White});

    board.setCastlingRights({false, false, false, false});

    EXPECT_EQ(
        FenGenerator::generate(board),
        "Q3k3/8/8/8/8/8/8/4K3 w - - 0 1"
    );
}

/**
 * @brief Castling rights must reflect any subset of the four flags,
 *        preserving KQkq ordering, and "-" when none remain.
 */
TEST(FenGeneratorTest, PartialCastlingRights)
{
    Board board;

    CastlingRights rights;
    rights.whiteKingSide  = true;
    rights.whiteQueenSide = false;
    rights.blackKingSide  = false;
    rights.blackQueenSide = true;

    board.setCastlingRights(rights);

    std::string fen = FenGenerator::generate(board);

    EXPECT_NE(fen.find(" Kq "), std::string::npos);
}

TEST(FenGeneratorTest, NoCastlingRights)
{
    Board board;
    board.setCastlingRights({false, false, false, false});

    std::string fen = FenGenerator::generate(board);

    EXPECT_NE(fen.find(" - "), std::string::npos);
}

/**
 * @brief The en passant target square must be encoded in algebraic
 *        notation, and omitted ("-") when not available.
 */
TEST(FenGeneratorTest, EnPassantTargetSquare)
{
    Board board;
    // White just played e2-e4: the en passant target square is e3.
    board.setEnPassantTarget(Square{5, 4});

    std::string fen = FenGenerator::generate(board);

    EXPECT_NE(fen.find(" e3 "), std::string::npos);
}

TEST(FenGeneratorTest, NoEnPassantTarget)
{
    Board board;
    board.setEnPassantTarget(std::nullopt);

    std::string fen = FenGenerator::generate(board);

    EXPECT_NE(fen.find(" - 0 1"), std::string::npos);
}

/**
 * @brief The halfmove clock must be serialized verbatim, so engines can
 *        correctly enforce the fifty-move rule.
 */
TEST(FenGeneratorTest, HalfmoveClock)
{
    Board board;
    board.setHalfmoveClock(37);

    std::string fen = FenGenerator::generate(board);

    EXPECT_NE(fen.find(" 37 "), std::string::npos);
}

/**
 * @brief The fullmove number must be serialized verbatim and must start
 *        counting from move 1, incrementing after black moves elsewhere
 *        in the Board State module.
 */
TEST(FenGeneratorTest, FullmoveNumber)
{
    Board board;
    board.setFullmoveNumber(42);

    std::string fen = FenGenerator::generate(board);

    EXPECT_TRUE(fen.ends_with(" 42"));
}

/**
 * @brief All fields combined must produce a single well-formed FEN string,
 *        matching the exact field order required by the UCI protocol.
 */
TEST(FenGeneratorTest, AllFieldsCombined)
{
    Board board = emptyBoard();

    board.setPiece({0, 4}, {PieceType::King, PieceColor::Black});
    board.setPiece({7, 4}, {PieceType::King, PieceColor::White});
    board.setPiece({3, 4}, {PieceType::Pawn, PieceColor::White});
    board.setPiece({3, 3}, {PieceType::Pawn, PieceColor::Black});

    board.setSideToMove(PieceColor::Black);
    board.setCastlingRights({true, false, false, true});
    board.setEnPassantTarget(Square{4, 4}); // row 4 -> rank 4, col 4 -> file e
    board.setHalfmoveClock(0);
    board.setFullmoveNumber(15);

    EXPECT_EQ(
        FenGenerator::generate(board),
        "4k3/8/8/3pP3/8/8/8/4K3 b Kq e4 0 15"
    );
}
