#pragma once

#include <array>

#include <SFML/Graphics.hpp>

#include "board/board.hpp"

class Renderer
{
public:
    Renderer();

    bool init();

    bool isOpen() const;

    void draw(const ac::chess::Board& board);

private:

    void processEvents();

    void drawBoard();

    void drawPieces(const ac::chess::Board& board);

    const sf::Texture& textureFor(const ac::chess::Piece& piece) const;

private:

    static constexpr float WINDOW_SIZE = 850.f;
    static constexpr float SQUARE_SIZE = WINDOW_SIZE / 8.f;

    sf::RenderWindow window_;

    sf::Texture boardTexture_;

    std::array<sf::Texture, 12> pieceTextures_;
};