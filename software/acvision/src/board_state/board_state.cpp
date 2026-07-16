#include "board_state/board_state.hpp"

namespace ac {

BoardState::BoardState() {
    
    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            m_board[row][col] = Piece{PieceType::None, PieceColor::None};
        }
    }
}

Piece BoardState::get_piece(int row, int col) const {
    
    if (row < 0 || row >= 8 || col < 0 || col >= 8) {
        return Piece{PieceType::None, PieceColor::None};
    }
    
    return m_board[row][col];
}

void BoardState::set_piece(int row, int col, const Piece& piece) {
    
    if (row >= 0 && row < 8 && col >= 0 && col < 8) {
        m_board[row][col] = piece;
    }
}

} // namespace ac