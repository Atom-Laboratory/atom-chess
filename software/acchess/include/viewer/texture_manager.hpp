#pragma once

class TextureManager
{
public:

    bool load();

    const sf::Texture& board() const;

    const sf::Texture& piece(PieceType, PieceColor) const;

private:

    sf::Texture boardTexture_;

    std::array<sf::Texture,12> pieces_;
};