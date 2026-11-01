#include <gtest/gtest.h>
#include "integration/engine_move.hpp"
#include "board/move_applier.hpp"
#include "board/move_validator.hpp"
#include "fen_generator/fen_generator.hpp"
#include <string>
#include <limits>

using namespace ac::chess;
using namespace ac::chess::engine;
using namespace ac::integration;

namespace {

Board kings(PieceColor side = PieceColor::White) {
    Board board;
    board.clear();
    board.setPiece({7, 4}, {PieceType::King, PieceColor::White});
    board.setPiece({0, 4}, {PieceType::King, PieceColor::Black});
    board.setSideToMove(side);
    board.setHalfmoveClock(9);
    board.setFullmoveNumber(23);
    return board;
}

void expectLegal(const Board& board, const std::string& token, const Move& expected) {
    SCOPED_TRACE(token);
    const auto original = board;
    const auto result = validateEngineMove(board, {UciStatus::Success, token});
    ASSERT_EQ(result.status, EngineMoveStatus::ValidMove);
    ASSERT_TRUE(result.move.has_value());
    EXPECT_EQ(*result.move, expected);
    EXPECT_EQ(result.uciStatus, UciStatus::Success);
    EXPECT_EQ(board, original);
    EXPECT_EQ(FenGenerator::generate(board), FenGenerator::generate(original));
    auto copy = board;
    MoveApplier::apply(copy, *result.move);
    EXPECT_EQ(MoveValidator::validate(board, copy, board.sideToMove()), result.move);
    Move untrustedFlags = expected;
    untrustedFlags.capture = !expected.capture;
    untrustedFlags.castle = !expected.castle;
    untrustedFlags.enPassant = !expected.enPassant;
    EXPECT_EQ(MoveValidator::validate(board, untrustedFlags), result.move);
    EXPECT_EQ(board, original);
}

void expectRejected(const Board& board, const std::string& token,
                    EngineMoveStatus status = EngineMoveStatus::IllegalMove) {
    SCOPED_TRACE(token);
    const auto original = board;
    const auto result = validateEngineMove(board, {UciStatus::Success, token});
    EXPECT_EQ(result.status, status);
    EXPECT_FALSE(result.move.has_value());
    EXPECT_EQ(result.uciStatus, UciStatus::Success);
    EXPECT_EQ(board, original);
    EXPECT_EQ(FenGenerator::generate(board), FenGenerator::generate(original));
}

TEST(EngineMoveTest, PawnAndKnightUseExistingOrientationAndPreserveState) {
    const Board board;
    expectLegal(board, "e2e4", Move{.from = {6, 4}, .to = {4, 4}});
    expectLegal(board, "g1f3", Move{.from = {7, 6}, .to = {5, 5}});
    const auto result = validateEngineMove(board, {UciStatus::Success, "e2e4"});
    ASSERT_TRUE(result.move.has_value());
    auto copy = board;
    MoveApplier::apply(copy, *result.move);
    EXPECT_EQ(FenGenerator::generate(copy),
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1");
}

TEST(EngineMoveTest, CaptureIsCanonical) {
    auto board = kings();
    board.setPiece({4, 4}, {PieceType::Pawn, PieceColor::White});
    board.setPiece({3, 3}, {PieceType::Knight, PieceColor::Black});
    expectLegal(board, "e4d5", Move{.from = {4, 4}, .to = {3, 3}, .capture = true});
}

TEST(EngineMoveTest, CastlesBothSidesForBothColors) {
    for (const auto side : {PieceColor::White, PieceColor::Black}) {
        for (const bool kingSide : {false, true}) {
            auto board = kings(side);
            const int row = side == PieceColor::White ? 7 : 0;
            const char rank = side == PieceColor::White ? '1' : '8';
            board.setPiece({row, kingSide ? 7 : 0}, {PieceType::Rook, side});
            const std::string token{'e', rank, kingSide ? 'g' : 'c', rank};
            expectLegal(board, token, Move{.from = {row, 4}, .to = {row, kingSide ? 6 : 2}, .castle = true});
        }
    }
}

TEST(EngineMoveTest, RejectsCastlingInCheckThroughCheckBlockedOrRevoked) {
    auto board = kings();
    board.setPiece({7, 7}, {PieceType::Rook, PieceColor::White});
    for (const int attackedColumn : {4, 5, 6}) {
        auto attacked = board;
        attacked.setPiece({3, attackedColumn}, {PieceType::Rook, PieceColor::Black});
        expectRejected(attacked, "e1g1");
    }
    auto blocked = board;
    blocked.setPiece({7, 5}, {PieceType::Bishop, PieceColor::White});
    expectRejected(blocked, "e1g1");
    auto revoked = board;
    revoked.setCastlingRights({false, true, true, true});
    expectRejected(revoked, "e1g1");
    expectRejected(kings(), "e1g1");
    expectRejected(board, "e1h1"); // Chess960 rook-square notation is not supported.
}

TEST(EngineMoveTest, EnPassantRequiresCurrentMetadataAndCapturedPawn) {
    auto board = kings();
    board.setPiece({3, 4}, {PieceType::Pawn, PieceColor::White});
    board.setPiece({3, 3}, {PieceType::Pawn, PieceColor::Black});
    board.setEnPassantTarget(Square{2, 3});
    expectLegal(board, "e5d6", Move{.from = {3, 4}, .to = {2, 3}, .capture = true, .enPassant = true});
    auto expired = board;
    expired.setEnPassantTarget(std::nullopt);
    expectRejected(expired, "e5d6");
    auto wrongTarget = board;
    wrongTarget.setEnPassantTarget(Square{2, 5});
    expectRejected(wrongTarget, "e5d6");
    auto missingPawn = board;
    missingPawn.setPiece({3, 3}, {});
    expectRejected(missingPawn, "e5d6");
    auto pinned = board;
    pinned.setPiece({0, 4}, {PieceType::Rook, PieceColor::Black});
    pinned.setPiece({0, 0}, {PieceType::King, PieceColor::Black});
    expectRejected(pinned, "e5d6");

    auto black = kings(PieceColor::Black);
    black.setPiece({4, 4}, {PieceType::Pawn, PieceColor::Black});
    black.setPiece({4, 5}, {PieceType::Pawn, PieceColor::White});
    black.setEnPassantTarget(Square{5, 5});
    expectLegal(black, "e4f3", Move{.from = {4, 4}, .to = {5, 5}, .capture = true, .enPassant = true});
}

TEST(EngineMoveTest, EnPassantRejectsEveryPromotionChoiceWithoutMutation) {
    for (const auto side : {PieceColor::White, PieceColor::Black}) {
        auto board = kings(side);
        const bool white = side == PieceColor::White;
        const Square source{white ? 3 : 4, 4};
        const Square target{white ? 2 : 5, 3};
        board.setPiece(source, {PieceType::Pawn, side});
        board.setPiece({source.row, target.col},
            {PieceType::Pawn, white ? PieceColor::Black : PieceColor::White});
        board.setEnPassantTarget(target);
        const auto original = board;
        const auto fen = FenGenerator::generate(board);
        for (const auto promotion : {PieceType::Pawn, PieceType::Knight, PieceType::Bishop,
                                    PieceType::Rook, PieceType::Queen, PieceType::King}) {
            SCOPED_TRACE(static_cast<int>(promotion));
            EXPECT_FALSE(MoveValidator::validate(board,
                Move{.from = source, .to = target, .promotion = promotion}).has_value());
            EXPECT_EQ(board, original);
            EXPECT_EQ(FenGenerator::generate(board), fen);
        }
    }
}

TEST(EngineMoveTest, PromotionsRequireExplicitAllowedTypeForBothColorsAndCaptures) {
    struct Promotion { char suffix; PieceType type; };
    const Promotion promotions[] = {{'q', PieceType::Queen}, {'r', PieceType::Rook},
                                    {'b', PieceType::Bishop}, {'n', PieceType::Knight}};
    for (const auto side : {PieceColor::White, PieceColor::Black}) {
        for (const bool capture : {false, true}) {
            auto board = kings(side);
            const bool white = side == PieceColor::White;
            const Square source{white ? 1 : 6, capture ? 1 : 0};
            const Square target{white ? 0 : 7, 0};
            board.setPiece(source, {PieceType::Pawn, side});
            if (capture) {
                board.setPiece(target, {PieceType::Rook, white ? PieceColor::Black : PieceColor::White});
            }
            const std::string token{capture ? 'b' : 'a', white ? '7' : '2', 'a', white ? '8' : '1'};
            for (const auto promotion : promotions) {
                expectLegal(board, token + promotion.suffix,
                    Move{.from = source, .to = target, .promotion = promotion.type, .capture = capture});
            }
            expectRejected(board, token);
            expectRejected(board, token + 'k', EngineMoveStatus::InvalidToken);
            EXPECT_FALSE(MoveValidator::validate(board,
                Move{.from = source, .to = target, .promotion = PieceType::King}).has_value());
        }
    }
    auto premature = kings();
    premature.setPiece({2, 0}, {PieceType::Pawn, PieceColor::White});
    expectRejected(premature, "a6a7q");
    auto nonPawn = kings();
    nonPawn.setPiece({1, 0}, {PieceType::Queen, PieceColor::White});
    expectRejected(nonPawn, "a7a8q");
}

TEST(EngineMoveTest, RejectsEmptyWrongSideBlockedOwnCaptureAndIllegalGeometry) {
    Board board;
    board.setHalfmoveClock(17);
    board.setFullmoveNumber(24);
    board.setEnPassantTarget(Square{5, 4});
    board.setCastlingRights({false, true, false, true});
    for (const auto* token : {"e3e4", "e7e5", "c1h6", "a1a4", "d1d4", "e1e2",
                             "e2e5", "g1g3", "e2e2", "e2e4q"}) {
        expectRejected(board, token);
    }
}

TEST(EngineMoveTest, RejectsKingCaptureExposedKingAndKingEnteringAttack) {
    auto board = kings();
    board.setPiece({0, 4}, {PieceType::Rook, PieceColor::Black});
    board.setPiece({0, 0}, {PieceType::King, PieceColor::Black});
    board.setPiece({6, 4}, {PieceType::Rook, PieceColor::White});
    expectRejected(board, "e2f2");
    board.setPiece({0, 5}, {PieceType::Rook, PieceColor::Black});
    expectRejected(board, "e1f1");
    auto kingCapture = kings();
    kingCapture.setPiece({1, 4}, {PieceType::Rook, PieceColor::White});
    expectRejected(kingCapture, "e7e8");
}

TEST(EngineMoveTest, InvalidTokensAndDirectCoordinatesNeverProduceMoves) {
    const Board board;
    for (const auto* token : {"", "e2e", "e2e4extra", "i2e4", "e0e4", "e2e9", "E2e4",
                             "a7a8Q", "e2e4 ", "(none)", "0000"}) {
        expectRejected(board, token, EngineMoveStatus::InvalidToken);
    }
    expectRejected(board, std::string{"e2\0e4", 5}, EngineMoveStatus::InvalidToken);
    const auto original = board;
    for (const auto proposal : {Move{.from = {-1, 0}, .to = {4, 0}},
                               Move{.from = {6, 0}, .to = {8, 0}},
                               Move{.from = {6, 0}, .to = {6, 0}}}) {
        EXPECT_FALSE(MoveValidator::validate(board, proposal).has_value());
    }
    EXPECT_EQ(board, original);
}

TEST(EngineMoveTest, NoMoveAndEveryCommunicationFailurePreserveUciStatus) {
    const Board board;
    const auto original = board;
    for (const auto status : {UciStatus::NoMove, UciStatus::Timeout, UciStatus::EndOfFile,
        UciStatus::ReadError, UciStatus::WriteError, UciStatus::MalformedResponse,
        UciStatus::BufferLimit, UciStatus::NotInitialized, UciStatus::InvalidRequest, UciStatus::Unsupported}) {
        const auto result = validateEngineMove(board, {status, "e2e4"});
        EXPECT_EQ(result.status, status == UciStatus::NoMove
            ? EngineMoveStatus::NoMove : EngineMoveStatus::CommunicationError);
        EXPECT_FALSE(result.move.has_value());
        EXPECT_EQ(result.uciStatus, status);
        EXPECT_EQ(board, original);
    }
}

TEST(EngineMoveTest, ValidatedBlackPromotionCaptureUpdatesAllFenFieldsOnCopy) {
    auto board = kings(PieceColor::Black);
    board.setPiece({6, 1}, {PieceType::Pawn, PieceColor::Black});
    board.setPiece({7, 0}, {PieceType::Rook, PieceColor::White});
    board.setEnPassantTarget(Square{5, 3});
    const auto original = board;
    const auto result = validateEngineMove(board, {UciStatus::Success, "b2a1n"});
    ASSERT_EQ(result.status, EngineMoveStatus::ValidMove);
    ASSERT_TRUE(result.move.has_value());
    auto copy = board;
    MoveApplier::apply(copy, *result.move);
    EXPECT_EQ(FenGenerator::generate(copy), "4k3/8/8/8/8/8/8/n3K3 w Kkq - 0 24");
    EXPECT_EQ(board, original);
}

TEST(EngineMoveTest, RejectsUnrepresentableFenCountersBeforeApplyingToCopy) {
    Board board;
    board.setHalfmoveClock(std::numeric_limits<int>::max());
    expectRejected(board, "g1f3");
    expectLegal(board, "e2e4", Move{.from = {6, 4}, .to = {4, 4}});
    board.setSideToMove(PieceColor::Black);
    board.setFullmoveNumber(std::numeric_limits<int>::max());
    expectRejected(board, "e7e5");
}

} // namespace
