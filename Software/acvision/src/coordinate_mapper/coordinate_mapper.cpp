#include "coordinate_mapper/coordinate_mapper.hpp"

#include <cmath>
#include <cctype>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace
{
    /**
     * @brief Constante matemática PI.
     */
    constexpr double PI = 3.14159265358979323846;
}

CoordinateMapper::CoordinateMapper(
    const std::string& config_file
)
    : origin_x(0.0),
      origin_y(0.0),
      square_size(0.0),
      rotation(0.0),
      calibrated(false),
      config_path(config_file)
{
    /*
     * O tabuleiro possui exatamente 64 casas.
     *
     * Reservamos espaço antecipadamente para evitar
     * realocações desnecessárias do unordered_map.
     */
    board_map.reserve(64);

    /*
     * Tenta carregar automaticamente a calibração.
     *
     * Se o arquivo não existir ou estiver inválido,
     * calibrated permanecerá false.
     */
    calibrated = loadCalibration();

    /*
     * loadCalibration() apenas carrega os parâmetros.
     *
     * Depois que eles são validados, geramos novamente
     * o mapa das 64 casas.
     */
    if (calibrated)
    {
        generateMap();
    }
}

bool CoordinateMapper::isCalibrated() const
{
    return calibrated;
}

void CoordinateMapper::calibrate(
    const Point2D& a1,
    const Point2D& h1
)
{
    /*
     * A1 representa a origem do sistema de coordenadas
     * do tabuleiro.
     */
    origin_x = a1.x;
    origin_y = a1.y;

    /*
     * Calcula o vetor que representa o primeiro eixo
     * do tabuleiro:
     *
     * A1 -> H1
     */
    const double dx = h1.x - a1.x;
    const double dy = h1.y - a1.y;

    /*
     * Calcula a distância física entre A1 e H1.
     */
    const double distance = std::sqrt(
        (dx * dx) +
        (dy * dy)
    );

    /*
     * A1 e H1 não podem ocupar a mesma posição.
     */
    if (distance <= 0.0)
    {
        throw std::runtime_error(
            "Os pontos A1 e H1 devem possuir coordenadas diferentes."
        );
    }

    /*
     * Entre A1 e H1 existem 7 intervalos:
     *
     * A1 B1 C1 D1 E1 F1 G1 H1
     *
     * Portanto:
     *
     * square_size = distancia / 7
     */
    square_size = distance / 7.0;

    /*
     * Determina a orientação do eixo X do tabuleiro.
     *
     * atan2 fornece o ângulo em radianos.
     */
    rotation = std::atan2(dy, dx);

    /*
     * Normaliza o ângulo para o intervalo [-PI, PI].
     *
     * atan2 já retorna esse intervalo, mas a normalização
     * mantém a intenção explícita.
     */
    if (rotation > PI)
    {
        rotation -= 2.0 * PI;
    }
    else if (rotation < -PI)
    {
        rotation += 2.0 * PI;
    }

    /*
     * Verifica se os parâmetros calculados são válidos.
     */
    if (!validateCalibration())
    {
        calibrated = false;

        throw std::runtime_error(
            "Os parâmetros calculados para a calibração são inválidos."
        );
    }

    calibrated = true;

    /*
     * Gera as coordenadas das 64 casas.
     */
    generateMap();

    /*
     * Persiste a calibração para as próximas execuções.
     */
    saveCalibration();
}

Point2D CoordinateMapper::getCoordinates(
    const std::string& square
) const
{
    /*
     * Não é possível consultar uma posição se o sistema
     * ainda não estiver calibrado.
     */
    if (!calibrated)
    {
        throw std::runtime_error(
            "Sistema de coordenadas não calibrado."
        );
    }

    /*
     * Uma casa válida possui exatamente dois caracteres:
     *
     * A1
     * E2
     * H8
     */
    if (square.size() != 2)
    {
        throw std::invalid_argument(
            "Casa do tabuleiro inválida: " + square
        );
    }

    /*
     * Copia a entrada para que possamos normalizá-la
     * sem modificar o argumento original.
     */
    std::string key = square;

    /*
     * Converte a coluna para maiúscula.
     *
     * e2 -> E2
     */
    key[0] = static_cast<char>(
        std::toupper(
            static_cast<unsigned char>(key[0])
        )
    );

    /*
     * A busca na tabela hash possui complexidade média O(1).
     */
    const auto it = board_map.find(key);

    if (it == board_map.end())
    {
        throw std::invalid_argument(
            "Casa do tabuleiro inválida: " + square
        );
    }

    return it->second;
}

void CoordinateMapper::generateMap()
{
    /*
     * Remove o mapa anterior caso exista.
     */
    board_map.clear();

    /*
     * O tabuleiro possui oito colunas:
     *
     * A B C D E F G H
     */
    constexpr char files[] = {
        'A', 'B', 'C', 'D',
        'E', 'F', 'G', 'H'
    };

    /*
     * Pré-calculamos seno e cosseno porque os mesmos valores
     * serão utilizados nas 64 casas.
     */
    const double cos_theta = std::cos(rotation);
    const double sin_theta = std::sin(rotation);

    /*
     * Percorre as oito colunas.
     */
    for (int file = 0; file < 8; ++file)
    {
        /*
         * Percorre as oito linhas.
         */
        for (int rank = 0; rank < 8; ++rank)
        {
            /*
             * Coordenadas no sistema local do tabuleiro.
             *
             * A1:
             *
             * localX = 0
             * localY = 0
             *
             * B1:
             *
             * localX = square_size
             * localY = 0
             *
             * A2:
             *
             * localX = 0
             * localY = square_size
             */
            const double local_x =
                static_cast<double>(file) * square_size;

            const double local_y =
                static_cast<double>(rank) * square_size;

            /*
             * Aplicação da transformação de rotação.
             *
             * [x']   [ cos -sin ] [x]
             * [y'] = [ sin  cos ] [y]
             */
            Point2D point;

            point.x =
                origin_x +
                (local_x * cos_theta) -
                (local_y * sin_theta);

            point.y =
                origin_y +
                (local_x * sin_theta) +
                (local_y * cos_theta);

            /*
             * Monta a identificação da casa.
             *
             * Exemplos:
             *
             * A1
             * E2
             * H8
             */
            std::string square;

            square += files[file];
            square += std::to_string(rank + 1);

            /*
             * Insere no mapa.
             */
            board_map[square] = point;
        }
    }
}

bool CoordinateMapper::validateCalibration() const
{
    /*
     * O tamanho da casa precisa ser positivo.
     */
    if (square_size <= 0.0)
    {
        return false;
    }

    /*
     * Verifica NaN.
     */
    if (std::isnan(origin_x) ||
        std::isnan(origin_y) ||
        std::isnan(square_size) ||
        std::isnan(rotation))
    {
        return false;
    }

    /*
     * Verifica infinito.
     */
    if (std::isinf(origin_x) ||
        std::isinf(origin_y) ||
        std::isinf(square_size) ||
        std::isinf(rotation))
    {
        return false;
    }

    return true;
}

void CoordinateMapper::saveCalibration() const
{
    /*
     * Abre o arquivo para escrita.
     *
     * O conteúdo anterior será substituído.
     */
    std::ofstream file(config_path);

    if (!file)
    {
        throw std::runtime_error(
            "Não foi possível salvar o arquivo de calibração: " +
            config_path
        );
    }

    /*
     * Utilizamos dez casas decimais para preservar precisão
     * suficiente para as coordenadas físicas.
     */
    file << std::fixed
         << std::setprecision(10);

    file << "origin_x="
         << origin_x
         << '\n';

    file << "origin_y="
         << origin_y
         << '\n';

    file << "square_size="
         << square_size
         << '\n';

    file << "rotation="
         << rotation
         << '\n';

    /*
     * O fechamento ocorre automaticamente quando o objeto
     * ofstream sai de escopo.
     */
}

bool CoordinateMapper::loadCalibration()
{
    /*
     * Tenta abrir o arquivo.
     *
     * Se ele não existir, significa que provavelmente
     * estamos executando pela primeira vez.
     */
    std::ifstream file(config_path);

    if (!file)
    {
        return false;
    }

    std::string line;

    /*
     * Lê o arquivo linha por linha.
     */
    while (std::getline(file, line))
    {
        /*
         * Ignora linhas vazias.
         */
        if (line.empty())
        {
            continue;
        }

        std::stringstream stream(line);

        std::string key;
        std::string value;

        /*
         * Divide:
         *
         * origin_x=150
         *
         * em:
         *
         * key   = origin_x
         * value = 150
         */
        if (!std::getline(stream, key, '='))
        {
            continue;
        }

        if (!std::getline(stream, value))
        {
            continue;
        }

        try
        {
            const double number =
                std::stod(value);

            if (key == "origin_x")
            {
                origin_x = number;
            }
            else if (key == "origin_y")
            {
                origin_y = number;
            }
            else if (key == "square_size")
            {
                square_size = number;
            }
            else if (key == "rotation")
            {
                rotation = number;
            }
        }
        catch (const std::exception&)
        {
            /*
             * Um valor inválido torna a calibração inválida.
             */
            calibrated = false;

            return false;
        }
    }

    /*
     * Verifica se todos os parâmetros carregados são válidos.
     */
    calibrated = validateCalibration();

    return calibrated;
}