#ifndef ACMOTION_COORDINATE_MAPPER_HPP
#define ACMOTION_COORDINATE_MAPPER_HPP

#include <cstddef>
#include <string>

namespace ac::motion {

/**
 * @struct Point2D
 * @brief Cartesian XY coordinate expressed in the SCARA base frame.
 *
 * All coordinates are expressed in millimetres.
 */
struct Point2D {
    double x{0.0}; ///< X coordinate in millimetres.
    double y{0.0}; ///< Y coordinate in millimetres.
};

/**
 * @enum RankDirection
 * @brief Orientation used to derive increasing chess ranks from the calibrated first rank.
 */
enum class RankDirection {
    COUNTERCLOCKWISE, ///< Rank direction is +90 degrees from the A1→H1 file axis.
    CLOCKWISE         ///< Rank direction is -90 degrees from the A1→H1 file axis.
};

/**
 * @enum GraveyardSide
 * @brief Identifies the physical graveyard associated with captured-piece color.
 */
enum class GraveyardSide {
    WHITE, ///< Graveyard used for captured White pieces.
    BLACK  ///< Graveyard used for captured Black pieces.
};

/**
 * @struct GridGeometry
 * @brief Affine geometry of a regular physical 2D slot grid.
 *
 * A slot is resolved as:
 * `origin + column * columnStep + row * rowStep`.
 *
 * All Point2D values are expressed in millimetres in the SCARA base frame.
 */
struct GridGeometry {
    Point2D origin{};      ///< Physical coordinate of grid slot {row=0, column=0}.
    Point2D columnStep{};  ///< XY displacement for one column increment.
    Point2D rowStep{};     ///< XY displacement for one row increment.
    std::size_t rows{2};   ///< Number of available rows.
    std::size_t columns{8};///< Number of available columns.
};

/**
 * @class CoordinateMapper
 * @brief Maps logical chess/graveyard locations to calibrated SCARA XY coordinates.
 *
 * CoordinateMapper runs on the Linux SBC and owns only geometric calibration.
 * It does not perform inverse kinematics, trajectory planning, chess legality,
 * motor control or ESP32 communication.
 *
 * The chessboard is assumed fixed relative to the SCARA base for the MVP.
 * Board calibration is defined by physical A1 and H1 coordinates plus the rank
 * orientation. Graveyards are configured independently as regular grids.
 */
class CoordinateMapper {
public:
    /**
     * @brief Creates a mapper and optionally associates it with a calibration file.
     * @param configPath Path used by saveCalibration()/loadCalibration().
     *
     * Passing an empty path is valid for test/in-memory calibration.
     */
    explicit CoordinateMapper(
        std::string configPath = "board_calibration.cfg"
    );

    /**
     * @brief Reports whether board geometry has been calibrated.
     * @return true after successful calibrateBoard() or loadCalibration().
     */
    bool isBoardCalibrated() const noexcept;

    /**
     * @brief Calibrates the fixed chessboard from the physical first-rank endpoints.
     * @param a1 Physical center of square A1 in the SCARA base frame.
     * @param h1 Physical center of square H1 in the SCARA base frame.
     * @param rankDirection Orientation of increasing ranks relative to A1→H1.
     *
     * The method derives square size and board rotation from A1/H1.
     *
     * @throws std::invalid_argument when coordinates are non-finite or A1/H1
     *         do not define a valid non-zero board axis.
     */
    void calibrateBoard(
        Point2D a1,
        Point2D h1,
        RankDirection rankDirection = RankDirection::COUNTERCLOCKWISE
    );

    /**
     * @brief Resolves one algebraic square to a physical XY coordinate.
     * @param square Two-character algebraic square, e.g. "a1" or "e4".
     * @return Square-center coordinate in millimetres in the SCARA base frame.
     * @throws std::runtime_error when the board is not calibrated.
     * @throws std::invalid_argument when square notation is invalid.
     */
    Point2D boardSquare(const std::string& square) const;

    /**
     * @brief Configures one captured-piece graveyard as a regular physical grid.
     * @param side Graveyard associated with captured White or Black pieces.
     * @param geometry Grid origin, steps and dimensions.
     * @throws std::invalid_argument when geometry is non-finite, degenerate or empty.
     */
    void setGraveyardGeometry(
        GraveyardSide side,
        const GridGeometry& geometry
    );

    /**
     * @brief Resolves one graveyard slot to a physical XY coordinate.
     * @param side Graveyard side.
     * @param row Zero-based logical grid row.
     * @param column Zero-based logical grid column.
     * @return Slot coordinate in millimetres in the SCARA base frame.
     * @throws std::runtime_error when that graveyard is not configured.
     * @throws std::out_of_range when row/column exceed configured dimensions.
     */
    Point2D graveyardSlot(
        GraveyardSide side,
        std::size_t row,
        std::size_t column
    ) const;

    /**
     * @brief Persists current calibration to configPath.
     * @return true when the file was written successfully.
     *
     * @note This method does not invent defaults for missing physical calibration.
     */
    bool saveCalibration() const;

    /**
     * @brief Loads calibration from configPath.
     * @return true when a complete valid calibration was loaded.
     *
     * Invalid or incomplete persisted geometry must not be treated as calibrated.
     */
    bool loadCalibration();

private:
    /**
     * @struct BoardGeometry
     * @brief Internal representation of fixed board calibration.
     */
    struct BoardGeometry {
        Point2D a1{}; ///< Physical A1 center.
        double squareSize{0.0}; ///< Derived chess-square spacing in millimetres.
        double rotationRadians{0.0}; ///< File-axis orientation in the base frame.
        RankDirection rankDirection{RankDirection::COUNTERCLOCKWISE}; ///< Rank orientation.
        bool calibrated{false}; ///< Whether board geometry is ready for lookup.
    };

    BoardGeometry board_{}; ///< Fixed-board calibration.
    GridGeometry whiteGraveyard_{}; ///< Captured-White storage geometry.
    GridGeometry blackGraveyard_{}; ///< Captured-Black storage geometry.
    bool whiteGraveyardConfigured_{false}; ///< White graveyard validity flag.
    bool blackGraveyardConfigured_{false}; ///< Black graveyard validity flag.
    std::string configPath_; ///< Persistence path for physical calibration.

    /**
     * @brief Checks that both coordinates of a point are finite.
     */
    static bool finite(Point2D point) noexcept;

    /**
     * @brief Validates grid dimensions and finite/non-degenerate step geometry.
     */
    static bool validGrid(const GridGeometry& geometry) noexcept;
};

} // namespace ac::motion

#endif
