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

std::vector<BoardChange> BoardState::compare_with(const BoardState& new_state) const {
    std::vector<BoardChange> changes;
    
    
    struct HalfChange {
        Piece piece;
        int row;
        int col;
    };
    
    std::vector<HalfChange> removed;
    std::vector<HalfChange> added;

    
    for (int row = 0; row < 8; ++row) {
        for (int col = 0; col < 8; ++col) {
            Piece old_p = this->m_board[row][col];
            Piece new_p = new_state.get_piece(row, col);

            
            bool is_same_piece = (old_p.type == new_p.type) && (old_p.color == new_p.color);

            if (!is_same_piece) {
                
                if (old_p.type != PieceType::None) {
                    removed.push_back({old_p, row, col});
                }
                
                if (new_p.type != PieceType::None) {
                    added.push_back({new_p, row, col});
                }
            }
        }
    }

    
    for (auto it_rem = removed.begin(); it_rem != removed.end(); ) {
        bool matched = false;
        
        for (auto it_add = added.begin(); it_add != added.end(); ++it_add) {
            
            if (it_rem->piece.type == it_add->piece.type && it_rem->piece.color == it_add->piece.color) {
                BoardChange move;
                move.piece = it_rem->piece;
                move.from_row = it_rem->row;
                move.from_col = it_rem->col;
                move.to_row = it_add->row;
                move.to_col = it_add->col;
                
                changes.push_back(move);
                
                
                added.erase(it_add);
                matched = true;
                break;
            }
        }
        
        if (matched) {
            it_rem = removed.erase(it_rem);
        } else {
            ++it_rem;
        }
    }

    
    for (const auto& rem : removed) {
        BoardChange capture;
        capture.piece = rem.piece;
        capture.from_row = rem.row;
        capture.from_col = rem.col;
        
        changes.push_back(capture);
    }

    
    for (const auto& add : added) {
        BoardChange spawn;
        spawn.piece = add.piece;
        
        spawn.to_row = add.row;
        spawn.to_col = add.col;
        changes.push_back(spawn);
    }

    return changes;
}
} // namespace ac