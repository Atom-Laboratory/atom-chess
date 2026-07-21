/**
 * @file chess.demo.cpp
 */

#include "board/board.hpp"
#include "viewer/renderer.hpp"

int main()
{
    Board board;
    board.reset();

    Renderer renderer;

    if (!renderer.init())
        return -1;

    // // Movimento de teste
    // board.setPiece(
    //     {4, 4},
    //     board.pieceAt({6, 4})
    // );

    // board.setPiece(
    //     {6, 4},
    //     {}
    // );

    while (renderer.isOpen())
    {
        renderer.draw(board);
        board.printBoard();
    }

    

    return 0;
}