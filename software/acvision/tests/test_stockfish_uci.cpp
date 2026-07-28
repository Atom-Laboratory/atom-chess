#include <gtest/gtest.h>
#include "stockfish_uci.hpp" 

TEST(StockfishUCITest, Inicializacao) {
    
    ac::StockfishUCI stockfish("stockfish"); 
    
    
    bool iniciou = stockfish.init();
    
    EXPECT_TRUE(iniciou); 
}

TEST(StockfishUCITest, RetornaMelhorJogada) {
    
    ac::StockfishUCI stockfish("stockfish");
    
    
    stockfish.init();
    
    std::string fen_inicial = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    
    std::string melhor_jogada = stockfish.get_best_move(fen_inicial, 5);
    
    ASSERT_FALSE(melhor_jogada.empty());
    EXPECT_GE(melhor_jogada.length(), 4);
}

TEST(StockfishUCITest, BestMoveIsCheckMate){
    ac::StockfishUCI stockfish("stockfish");
    stockfish.init();

    std::string fen = "6k1/5ppp/8/8/8/5Q2/6PP/6K1 w - - 0 1";

    std::string best_move = stockfish.get_best_move(fen,15);

    std::cout << "best_move: " + best_move ;
    EXPECT_EQ(best_move, "f3a8");
}
