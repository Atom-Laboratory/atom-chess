#include "viewer/renderer.hpp"
#include "utils/path.hpp"

#include <stdexcept>

Renderer::Renderer()
{
}

bool Renderer::init()
{
    window_.create(
        sf::VideoMode({850, 850}),
        "ATOM Chess"
    );

    if (!boardTexture_.loadFromFile("assets/board.png"))
        if (!boardTexture_.loadFromFile(
        utils::assetPath("board.png").string()))
    {
        return false;
    }

    const char* names[12] =
    {
        "wp","wn","wb","wr","wq","wk",
        "bp","bn","bb","br","bq","bk"
    };

    for (int i = 0; i < 12; i++)
    {
        auto path = utils::assetPath(
            std::string("pieces/") + names[i] + ".png"
        );

        if (!pieceTextures_[i].loadFromFile(path.string()))
        {
            return false;
        }
    }

    return true;
}

bool Renderer::isOpen() const
{
    return window_.isOpen();
}

void Renderer::processEvents()
{
    while (const auto event = window_.pollEvent())
    {
        if (event->is<sf::Event::Closed>())
            window_.close();
    }
}

void Renderer::drawBoard()
{
    sf::Sprite board(boardTexture_);

    auto size = boardTexture_.getSize();

    board.setScale({
        WINDOW_SIZE / static_cast<float>(size.x),
        WINDOW_SIZE / static_cast<float>(size.y)
    });

    window_.draw(board);
}

const sf::Texture& Renderer::textureFor(const Piece& piece) const
{
    int offset = (piece.color == PieceColor::White) ? 0 : 6;

    switch (piece.type)
    {
        case PieceType::Pawn:   return pieceTextures_[offset + 0];
        case PieceType::Knight: return pieceTextures_[offset + 1];
        case PieceType::Bishop: return pieceTextures_[offset + 2];
        case PieceType::Rook:   return pieceTextures_[offset + 3];
        case PieceType::Queen:  return pieceTextures_[offset + 4];
        case PieceType::King:   return pieceTextures_[offset + 5];
        default:                return pieceTextures_[0];
    }
}

void Renderer::drawPieces(const Board& board)
{
    for (int row = 0; row < 8; row++)
    {
        for (int col = 0; col < 8; col++)
        {
            Piece piece = board.pieceAt({row, col});

            if (piece.type == PieceType::None)
                continue;

            const sf::Texture& texture = textureFor(piece);

            sf::Sprite sprite(texture);

            auto size = texture.getSize();

            sprite.setScale({
                SQUARE_SIZE / static_cast<float>(size.x),
                SQUARE_SIZE / static_cast<float>(size.y)
            });

            sprite.setPosition({
                col * SQUARE_SIZE,
                row * SQUARE_SIZE
            });

            window_.draw(sprite);
        }
    }
}
void Renderer::draw(const Board& board)
{
    processEvents();

    window_.clear();

    drawBoard();

    drawPieces(board);

    window_.display();
}