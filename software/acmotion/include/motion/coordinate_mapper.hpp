#ifndef ACMOTION_COORDINATE_MAPPER_HPP
#define ACMOTION_COORDINATE_MAPPER_HPP

#include <cstddef>
#include <string>

namespace ac::motion {

struct Point2D {
    double x{0.0};
    double y{0.0};
};

enum class RankDirection {
    COUNTERCLOCKWISE,
    CLOCKWISE
};

enum class GraveyardSide {
    WHITE,
    BLACK
};

struct GridGeometry {
    Point2D origin{};
    Point2D columnStep{};
    Point2D rowStep{};
    std::size_t rows{2};
    std::size_t columns{8};
};

class CoordinateMapper {
public:
    explicit CoordinateMapper(
        std::string configPath = "board_calibration.cfg"
    );

    bool isBoardCalibrated() const noexcept;

    void calibrateBoard(
        Point2D a1,
        Point2D h1,
        RankDirection rankDirection = RankDirection::COUNTERCLOCKWISE
    );

    Point2D boardSquare(const std::string& square) const;

    void setGraveyardGeometry(GraveyardSide side, const GridGeometry& geometry);

    Point2D graveyardSlot(
        GraveyardSide side,
        std::size_t row,
        std::size_t column
    ) const;

    bool saveCalibration() const;
    bool loadCalibration();

private:
    struct BoardGeometry {
        Point2D a1{};
        double squareSize{0.0};
        double rotationRadians{0.0};
        RankDirection rankDirection{RankDirection::COUNTERCLOCKWISE};
        bool calibrated{false};
    };

    BoardGeometry board_{};
    GridGeometry whiteGraveyard_{};
    GridGeometry blackGraveyard_{};
    bool whiteGraveyardConfigured_{false};
    bool blackGraveyardConfigured_{false};
    std::string configPath_;

    static bool finite(Point2D point) noexcept;
    static bool validGrid(const GridGeometry& geometry) noexcept;
};

} // namespace ac::motion

#endif
