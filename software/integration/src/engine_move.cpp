#include "integration/engine_move.hpp"
#include "board/move_validator.hpp"

namespace ac::integration {

EngineMoveResult validateEngineMove(const chess::Board& officialBoard, const chess::engine::UciResult& response)
{
    if (response.status == chess::engine::UciStatus::NoMove) {
        return {EngineMoveStatus::NoMove, std::nullopt, response.status};
    }
    if (response.status != chess::engine::UciStatus::Success) {
        return {EngineMoveStatus::CommunicationError, std::nullopt, response.status};
    }
    const auto& token = response.move;
    if (token.size() != 4 && token.size() != 5) {
        return {EngineMoveStatus::InvalidToken, std::nullopt, response.status};
    }
    for (const int offset : {0, 2}) {
        if (token[offset] < 'a' || token[offset] > 'h' || token[offset + 1] < '1' || token[offset + 1] > '8') {
            return {EngineMoveStatus::InvalidToken, std::nullopt, response.status};
        }
    }
    chess::Move proposal{.from = {'8' - token[1], token[0] - 'a'},
                         .to = {'8' - token[3], token[2] - 'a'}};
    if (token.size() == 5) {
        switch (token[4]) {
        case 'q': proposal.promotion = chess::PieceType::Queen; break;
        case 'r': proposal.promotion = chess::PieceType::Rook; break;
        case 'b': proposal.promotion = chess::PieceType::Bishop; break;
        case 'n': proposal.promotion = chess::PieceType::Knight; break;
        default: return {EngineMoveStatus::InvalidToken, std::nullopt, response.status};
        }
    }
    const auto move = chess::MoveValidator::validate(officialBoard, proposal);
    return {move ? EngineMoveStatus::ValidMove : EngineMoveStatus::IllegalMove, move, response.status};
}

} // namespace ac::integration
