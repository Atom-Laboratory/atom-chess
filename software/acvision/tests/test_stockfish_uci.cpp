#include <gtest/gtest.h>
#include "stockfish_uci.hpp" 


TEST(StockfishUCITest, Inicializacao) {
    
    StockfishUCI stockfish;
    
    
    SUCCEED(); 
}


TEST(StockfishUCITest, RetornaMelhorJogada) {
    StockfishUCI stockfish;
    
    
    std::string fen_inicial = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    
    
    std::string melhor_jogada = stockfish.get_best_move(fen_inicial, 5);

    
    EXPECT_FALSE(melhor_jogada.empty());
    
    
    EXPECT_GE(melhor_jogada.length(), 4);
}