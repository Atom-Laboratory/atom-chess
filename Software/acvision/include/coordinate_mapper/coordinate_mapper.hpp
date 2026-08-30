#ifndef COORDINATE_MAPPER_HPP
#define COORDINATE_MAPPER_HPP

#include <string>
#include <unordered_map>

/**
 * @brief Representa uma coordenada física no plano XY.
 *
 * As coordenadas são expressas no sistema de coordenadas
 * utilizado pelo robô SCARA.
 */
struct Point2D
{
    double x;
    double y;
};

/**
 * @brief Realiza o mapeamento entre as casas do tabuleiro
 *        e as coordenadas físicas do robô.
 *
 * O CoordinateMapper é responsável por:
 *
 * - realizar a calibração do tabuleiro;
 * - determinar a origem do tabuleiro;
 * - determinar a orientação do tabuleiro;
 * - determinar o tamanho físico das casas;
 * - gerar as coordenadas das 64 casas;
 * - armazenar os parâmetros de calibração;
 * - carregar uma calibração previamente salva;
 * - converter uma casa de xadrez em coordenadas físicas.
 *
 * A calibração é realizada utilizando dois pontos físicos:
 *
 * A1 -> origem do tabuleiro
 * H1 -> extremidade do primeiro eixo
 *
 * A partir desses pontos são determinados:
 *
 * - origem;
 * - tamanho da casa;
 * - rotação do tabuleiro.
 */
class CoordinateMapper
{
public:

    /**
     * @brief Construtor.
     *
     * Tenta carregar automaticamente uma calibração existente.
     *
     * @param config_file Caminho do arquivo de calibração.
     */
    explicit CoordinateMapper(
        const std::string& config_file = "board_calibration.cfg"
    );

    /**
     * @brief Verifica se existe uma calibração válida.
     *
     * @return true se o sistema estiver calibrado.
     */
    bool isCalibrated() const;

    /**
     * @brief Realiza a calibração do tabuleiro.
     *
     * A1 representa a origem do sistema de coordenadas
     * do tabuleiro.
     *
     * H1 é utilizado para determinar:
     *
     * - tamanho físico das casas;
     * - orientação do eixo X do tabuleiro.
     *
     * @param a1 Coordenada física da casa A1.
     * @param h1 Coordenada física da casa H1.
     *
     * @throws std::runtime_error se os pontos forem inválidos.
     */
    void calibrate(
        const Point2D& a1,
        const Point2D& h1
    );

    /**
     * @brief Retorna as coordenadas físicas de uma casa.
     *
     * Exemplos:
     *
     * E2
     * a1
     * H8
     *
     * A entrada é convertida automaticamente para maiúsculas.
     *
     * @param square Casa do tabuleiro.
     *
     * @return Coordenada física da casa.
     *
     * @throws std::runtime_error se não houver calibração.
     * @throws std::invalid_argument se a casa for inválida.
     */
    Point2D getCoordinates(
        const std::string& square
    ) const;

private:

    /**
     * @brief Coordenada X da origem do tabuleiro.
     */
    double origin_x;

    /**
     * @brief Coordenada Y da origem do tabuleiro.
     */
    double origin_y;

    /**
     * @brief Tamanho físico de uma casa.
     */
    double square_size;

    /**
     * @brief Rotação do tabuleiro em radianos.
     */
    double rotation;

    /**
     * @brief Indica se existe uma calibração válida.
     */
    bool calibrated;

    /**
     * @brief Caminho do arquivo de configuração.
     */
    std::string config_path;

    /**
     * @brief Mapa das 64 casas do tabuleiro.
     *
     * A chave representa a casa:
     *
     * A1, A2, ..., H8
     *
     * O valor representa a coordenada física correspondente.
     */
    std::unordered_map<
        std::string,
        Point2D
    > board_map;

    /**
     * @brief Gera o mapa das 64 casas.
     *
     * Utiliza os parâmetros de calibração para transformar
     * as coordenadas locais do tabuleiro em coordenadas
     * físicas do robô.
     */
    void generateMap();

    /**
     * @brief Salva os parâmetros de calibração.
     *
     * O arquivo utiliza o formato:
     *
     * origin_x=...
     * origin_y=...
     * square_size=...
     * rotation=...
     *
     * @throws std::runtime_error se não for possível salvar.
     */
    void saveCalibration() const;

    /**
     * @brief Carrega os parâmetros de calibração.
     *
     * @return true se os parâmetros forem carregados e válidos.
     */
    bool loadCalibration();

    /**
     * @brief Valida os parâmetros de calibração.
     *
     * Verifica valores inválidos, NaN, infinito e tamanho
     * de casa menor ou igual a zero.
     *
     * @return true se a calibração for válida.
     */
    bool validateCalibration() const;
};

#endif // COORDINATE_MAPPER_HPP