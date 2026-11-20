#include <gtest/gtest.h>

#include <cctype>
#include <cstdio>
#include <string>

#include "board/board.hpp"
#include "board/move_applier.hpp"
#include "engine/stockfish_uci.hpp"
#include "fen_generator/fen_generator.hpp"

TEST(StockfishUCITest, Inicializacao) {
    ac::chess::engine::StockfishUCI stockfish(STOCKFISH_EXECUTABLE_PATH);
    bool iniciou = stockfish.init();
    EXPECT_TRUE(iniciou); 
}

TEST(StockfishUCITest, RetornaMelhorJogada) {
    ac::chess::engine::StockfishUCI stockfish(STOCKFISH_EXECUTABLE_PATH);
    stockfish.init();
    
    std::string fen_inicial = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    std::string melhor_jogada = stockfish.get_best_move(fen_inicial, 5);
    
    ASSERT_FALSE(melhor_jogada.empty());
    EXPECT_GE(melhor_jogada.length(), 4);
}

TEST(StockfishUCITest, BestMoveIsCheckMate){
    ac::chess::engine::StockfishUCI stockfish(STOCKFISH_EXECUTABLE_PATH);
    stockfish.init();

    std::string fen = "6k1/5ppp/8/8/8/5Q2/6PP/6K1 w - - 0 1";
    std::string best_move = stockfish.get_best_move(fen,15);

    std::cout << "best_move: " << best_move << std::endl;
    EXPECT_EQ(best_move, "f3a8");
}

// ---------------------------------------------------------------------------
// Issue #64 - validate FenGenerator output (after promotion) with Stockfish
//
// The tests above feed Stockfish hand-written FEN strings. These feed it the
// FEN produced by FenGenerator from a real Board transition, so a regression in
// serialization is caught by an independent FEN parser.
// ---------------------------------------------------------------------------
namespace {

using ac::chess::Board;
using ac::chess::CastlingRights;
using ac::chess::FenGenerator;
using ac::chess::Move;
using ac::chess::MoveApplier;
using ac::chess::Piece;
using ac::chess::PieceColor;
using ac::chess::PieceType;
using ac::chess::engine::UciStatus;

/** What Stockfish's own `d` command reports about a position it parsed. */
struct StockfishView {
    bool parsed{false};
    std::string fen;       ///< Position re-serialized by Stockfish.
    std::string checkers;  ///< Squares giving check ("" when not in check).
};

std::string trimmed(std::string text)
{
    while (!text.empty()
           && std::isspace(static_cast<unsigned char>(text.back()))) {
        text.pop_back();
    }

    std::size_t first = 0;
    while (first < text.size()
           && std::isspace(static_cast<unsigned char>(text[first]))) {
        ++first;
    }
    return text.substr(first);
}

/**
 * @brief Loads a FEN into a standalone Stockfish process and reads it back.
 *
 * Stockfish prints the position it actually understood, which makes it an
 * independent FEN parser. Note that Stockfish drops an en-passant square when
 * no capture is possible, so round-trip comparisons here use positions
 * without a pending en-passant target.
 */
StockfishView inspectWithStockfish(const std::string& fen)
{
    // The FEN is interpolated into a shell command: accept FEN characters only.
    for (const char c : fen) {
        const bool allowed = std::isalnum(static_cast<unsigned char>(c)) != 0
            || c == '/' || c == ' ' || c == '-';
        if (!allowed) {
            return {};
        }
    }

    const std::string command = "printf 'position fen " + fen
        + "\\nd\\nquit\\n' | '" + STOCKFISH_EXECUTABLE_PATH + "' 2>/dev/null";

    std::FILE* pipe = popen(command.c_str(), "r");
    if (pipe == nullptr) {
        return {};
    }

    StockfishView view;
    char buffer[512];
    while (std::fgets(buffer, sizeof buffer, pipe) != nullptr) {
        const std::string line = buffer;
        if (line.rfind("Fen: ", 0) == 0) {
            view.fen = trimmed(line.substr(5));
            view.parsed = true;
        } else if (line.rfind("Checkers:", 0) == 0) {
            view.checkers = trimmed(line.substr(9));
        }
    }
    (void)pclose(pipe);
    return view;
}

/** Bare board: two kings, one pawn one step from promotion, no castling. */
Board makePromotionBoard(PieceColor color)
{
    Board board;
    board.clear();
    board.setCastlingRights(CastlingRights{false, false, false, false});
    board.setSideToMove(color);
    board.setFullmoveNumber(40);

    if (color == PieceColor::White) {
        board.setPiece({7, 4}, {PieceType::King, PieceColor::White});  // e1
        board.setPiece({3, 7}, {PieceType::King, PieceColor::Black});  // h5
        board.setPiece({1, 0}, {PieceType::Pawn, PieceColor::White});  // a7
    } else {
        board.setPiece({0, 4}, {PieceType::King, PieceColor::Black});  // e8
        board.setPiece({4, 7}, {PieceType::King, PieceColor::White});  // h4
        board.setPiece({6, 0}, {PieceType::Pawn, PieceColor::Black});  // a2
    }
    return board;
}

Move promotionMove(PieceColor color, PieceType promotion)
{
    return color == PieceColor::White
        ? Move{.from = {1, 0}, .to = {0, 0}, .promotion = promotion}
        : Move{.from = {6, 0}, .to = {7, 0}, .promotion = promotion};
}

} // namespace

TEST(FenPromotionStockfishTest, StockfishAcceptsGeneratedFenForEveryPromotion)
{
    ac::chess::engine::StockfishUCI stockfish(STOCKFISH_EXECUTABLE_PATH);
    ASSERT_TRUE(stockfish.init());

    for (const PieceColor color : {PieceColor::White, PieceColor::Black}) {
        for (const PieceType piece : {PieceType::Queen, PieceType::Rook,
                                      PieceType::Bishop, PieceType::Knight}) {
            SCOPED_TRACE(::testing::Message()
                << (color == PieceColor::White ? "White" : "Black")
                << " promotes to piece #" << static_cast<int>(piece));

            Board board = makePromotionBoard(color);
            MoveApplier::apply(board, promotionMove(color, piece));
            const std::string fen = FenGenerator::generate(board);

            // Independent parser: Stockfish must read back exactly this FEN.
            const StockfishView view = inspectWithStockfish(fen);
            ASSERT_TRUE(view.parsed) << "Stockfish did not parse: " << fen;
            EXPECT_EQ(view.fen, fen);

            // The engine must also be able to search the resulting position.
            const auto result = stockfish.request_best_move(fen, 5);
            EXPECT_EQ(result.status, UciStatus::Success) << fen;
            EXPECT_FALSE(result.move.empty()) << fen;
        }
    }
}

TEST(FenPromotionStockfishTest, StockfishSeesPromotedPieceTypeThroughCheck)
{
    // White pawn f7 and black king h7. f8=N gives check (knight f8 hits h7);
    // f8=Q does not. If FenGenerator wrote the wrong piece letter, Stockfish
    // would disagree about who is in check.
    const auto promoteOnF8 = [](PieceType piece) {
        Board board;
        board.clear();
        board.setCastlingRights(CastlingRights{false, false, false, false});
        board.setPiece({7, 4}, {PieceType::King, PieceColor::White});  // e1
        board.setPiece({1, 7}, {PieceType::King, PieceColor::Black});  // h7
        board.setPiece({1, 5}, {PieceType::Pawn, PieceColor::White});  // f7
        MoveApplier::apply(board, Move{
            .from = {1, 5}, .to = {0, 5}, .promotion = piece
        });
        return FenGenerator::generate(board);
    };

    const std::string knightFen = promoteOnF8(PieceType::Knight);
    EXPECT_EQ(knightFen, "5N2/7k/8/8/8/8/8/4K3 b - - 0 1");
    const StockfishView knightView = inspectWithStockfish(knightFen);
    ASSERT_TRUE(knightView.parsed);
    EXPECT_EQ(knightView.fen, knightFen);
    EXPECT_EQ(knightView.checkers, "f8");

    const std::string queenFen = promoteOnF8(PieceType::Queen);
    EXPECT_EQ(queenFen, "5Q2/7k/8/8/8/8/8/4K3 b - - 0 1");
    const StockfishView queenView = inspectWithStockfish(queenFen);
    ASSERT_TRUE(queenView.parsed);
    EXPECT_EQ(queenView.fen, queenFen);
    EXPECT_TRUE(queenView.checkers.empty());
}

TEST(FenPromotionStockfishTest, StockfishAgreesOnCastlingAfterPromotionCapture)
{
    // bxa8=Q captures the a8 rook: only black's king-side right ("k") remains.
    Board board;
    board.clear();
    board.setCastlingRights(CastlingRights{false, false, true, true});
    board.setPiece({7, 4}, {PieceType::King, PieceColor::White});  // e1
    board.setPiece({0, 4}, {PieceType::King, PieceColor::Black});  // e8
    board.setPiece({0, 0}, {PieceType::Rook, PieceColor::Black});  // a8
    board.setPiece({0, 7}, {PieceType::Rook, PieceColor::Black});  // h8
    board.setPiece({1, 1}, {PieceType::Pawn, PieceColor::White});  // b7

    MoveApplier::apply(board, Move{
        .from = {1, 1}, .to = {0, 0},
        .promotion = PieceType::Queen, .capture = true
    });

    const std::string fen = FenGenerator::generate(board);
    EXPECT_EQ(fen, "Q3k2r/8/8/8/8/8/8/4K3 b k - 0 1");

    const StockfishView view = inspectWithStockfish(fen);
    ASSERT_TRUE(view.parsed);
    EXPECT_EQ(view.fen, fen);       // Stockfish keeps "k" and no "q".
    EXPECT_EQ(view.checkers, "a8"); // New queen checks the black king on e8.
}
