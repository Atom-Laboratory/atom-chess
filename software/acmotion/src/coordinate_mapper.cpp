#include "motion/coordinate_mapper.hpp"

#include <cmath>
#include <cctype>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>
#include <utility>

namespace ac::motion {

namespace {

Point2D add(Point2D lhs, Point2D rhs)
{
    return {lhs.x + rhs.x, lhs.y + rhs.y};
}

Point2D scale(Point2D value, double factor)
{
    return {value.x * factor, value.y * factor};
}

} // namespace

CoordinateMapper::CoordinateMapper(std::string configPath)
    : configPath_(std::move(configPath))
{
    loadCalibration();
}

bool CoordinateMapper::isBoardCalibrated() const noexcept
{
    return board_.calibrated;
}

bool CoordinateMapper::finite(Point2D point) noexcept
{
    return std::isfinite(point.x) && std::isfinite(point.y);
}

bool CoordinateMapper::validGrid(const GridGeometry& geometry) noexcept
{
    return finite(geometry.origin) &&
           finite(geometry.columnStep) &&
           finite(geometry.rowStep) &&
           geometry.rows > 0 &&
           geometry.columns > 0;
}

void CoordinateMapper::calibrateBoard(
    Point2D a1,
    Point2D h1,
    RankDirection rankDirection)
{
    if (!finite(a1) || !finite(h1)) {
        throw std::invalid_argument("Board calibration points must be finite.");
    }

    const double dx = h1.x - a1.x;
    const double dy = h1.y - a1.y;
    const double distance = std::hypot(dx, dy);

    if (!(distance > 0.0)) {
        throw std::invalid_argument("A1 and H1 must be different physical points.");
    }

    board_.a1 = a1;
    board_.squareSize = distance / 7.0;
    board_.rotationRadians = std::atan2(dy, dx);
    board_.rankDirection = rankDirection;
    board_.calibrated = true;

    if (!saveCalibration()) {
        throw std::runtime_error("Unable to persist board calibration.");
    }
}

Point2D CoordinateMapper::boardSquare(const std::string& square) const
{
    if (!board_.calibrated) {
        throw std::runtime_error("Board coordinate system is not calibrated.");
    }

    if (square.size() != 2) {
        throw std::invalid_argument("Invalid chess square: " + square);
    }

    const char fileChar = static_cast<char>(
        std::toupper(static_cast<unsigned char>(square[0]))
    );
    const char rankChar = square[1];

    if (fileChar < 'A' || fileChar > 'H' || rankChar < '1' || rankChar > '8') {
        throw std::invalid_argument("Invalid chess square: " + square);
    }

    const int file = fileChar - 'A';
    const int rank = rankChar - '1';

    const double cosTheta = std::cos(board_.rotationRadians);
    const double sinTheta = std::sin(board_.rotationRadians);

    const Point2D fileStep{
        board_.squareSize * cosTheta,
        board_.squareSize * sinTheta
    };

    const double rankSign =
        board_.rankDirection == RankDirection::COUNTERCLOCKWISE ? 1.0 : -1.0;

    const Point2D rankStep{
        rankSign * -board_.squareSize * sinTheta,
        rankSign *  board_.squareSize * cosTheta
    };

    return add(
        board_.a1,
        add(scale(fileStep, file), scale(rankStep, rank))
    );
}

void CoordinateMapper::setGraveyardGeometry(
    GraveyardSide side,
    const GridGeometry& geometry)
{
    if (!validGrid(geometry)) {
        throw std::invalid_argument("Invalid graveyard grid geometry.");
    }

    if (side == GraveyardSide::WHITE) {
        whiteGraveyard_ = geometry;
        whiteGraveyardConfigured_ = true;
    } else {
        blackGraveyard_ = geometry;
        blackGraveyardConfigured_ = true;
    }

    if (!saveCalibration()) {
        throw std::runtime_error("Unable to persist graveyard geometry.");
    }
}

Point2D CoordinateMapper::graveyardSlot(
    GraveyardSide side,
    std::size_t row,
    std::size_t column) const
{
    const GridGeometry* geometry = nullptr;
    bool configured = false;

    if (side == GraveyardSide::WHITE) {
        geometry = &whiteGraveyard_;
        configured = whiteGraveyardConfigured_;
    } else {
        geometry = &blackGraveyard_;
        configured = blackGraveyardConfigured_;
    }

    if (!configured) {
        throw std::runtime_error("Requested graveyard geometry is not configured.");
    }

    if (row >= geometry->rows || column >= geometry->columns) {
        throw std::out_of_range("Graveyard slot is outside the configured grid.");
    }

    return add(
        geometry->origin,
        add(scale(geometry->rowStep, static_cast<double>(row)),
            scale(geometry->columnStep, static_cast<double>(column)))
    );
}

bool CoordinateMapper::saveCalibration() const
{
    if (configPath_.empty()) {
        return true;
    }

    std::ofstream file(configPath_);
    if (!file) {
        return false;
    }

    file << std::setprecision(17);
    file << "version=1
";
    file << "board_calibrated=" << static_cast<int>(board_.calibrated) << '
';
    file << "board_a1_x=" << board_.a1.x << '
';
    file << "board_a1_y=" << board_.a1.y << '
';
    file << "board_square_size=" << board_.squareSize << '
';
    file << "board_rotation=" << board_.rotationRadians << '
';
    file << "board_rank_direction="
         << (board_.rankDirection == RankDirection::COUNTERCLOCKWISE ? 1 : -1)
         << '
';

    const auto writeGrid = [&file](const char* prefix, bool configured, const GridGeometry& g) {
        file << prefix << "_configured=" << static_cast<int>(configured) << '
';
        file << prefix << "_origin_x=" << g.origin.x << '
';
        file << prefix << "_origin_y=" << g.origin.y << '
';
        file << prefix << "_column_x=" << g.columnStep.x << '
';
        file << prefix << "_column_y=" << g.columnStep.y << '
';
        file << prefix << "_row_x=" << g.rowStep.x << '
';
        file << prefix << "_row_y=" << g.rowStep.y << '
';
        file << prefix << "_rows=" << g.rows << '
';
        file << prefix << "_columns=" << g.columns << '
';
    };

    writeGrid("white_graveyard", whiteGraveyardConfigured_, whiteGraveyard_);
    writeGrid("black_graveyard", blackGraveyardConfigured_, blackGraveyard_);
    return true;
}

bool CoordinateMapper::loadCalibration()
{
    if (configPath_.empty()) {
        return false;
    }

    std::ifstream file(configPath_);
    if (!file) {
        return false;
    }

    std::string key;
    while (std::getline(file, key, '=')) {
        std::string value;
        if (!std::getline(file, value)) {
            return false;
        }

        try {
            if (key == "board_calibrated") board_.calibrated = std::stoi(value) != 0;
            else if (key == "board_a1_x") board_.a1.x = std::stod(value);
            else if (key == "board_a1_y") board_.a1.y = std::stod(value);
            else if (key == "board_square_size") board_.squareSize = std::stod(value);
            else if (key == "board_rotation") board_.rotationRadians = std::stod(value);
            else if (key == "board_rank_direction") {
                board_.rankDirection = std::stoi(value) >= 0
                    ? RankDirection::COUNTERCLOCKWISE
                    : RankDirection::CLOCKWISE;
            }
            else if (key == "white_graveyard_configured") whiteGraveyardConfigured_ = std::stoi(value) != 0;
            else if (key == "white_graveyard_origin_x") whiteGraveyard_.origin.x = std::stod(value);
            else if (key == "white_graveyard_origin_y") whiteGraveyard_.origin.y = std::stod(value);
            else if (key == "white_graveyard_column_x") whiteGraveyard_.columnStep.x = std::stod(value);
            else if (key == "white_graveyard_column_y") whiteGraveyard_.columnStep.y = std::stod(value);
            else if (key == "white_graveyard_row_x") whiteGraveyard_.rowStep.x = std::stod(value);
            else if (key == "white_graveyard_row_y") whiteGraveyard_.rowStep.y = std::stod(value);
            else if (key == "white_graveyard_rows") whiteGraveyard_.rows = static_cast<std::size_t>(std::stoul(value));
            else if (key == "white_graveyard_columns") whiteGraveyard_.columns = static_cast<std::size_t>(std::stoul(value));
            else if (key == "black_graveyard_configured") blackGraveyardConfigured_ = std::stoi(value) != 0;
            else if (key == "black_graveyard_origin_x") blackGraveyard_.origin.x = std::stod(value);
            else if (key == "black_graveyard_origin_y") blackGraveyard_.origin.y = std::stod(value);
            else if (key == "black_graveyard_column_x") blackGraveyard_.columnStep.x = std::stod(value);
            else if (key == "black_graveyard_column_y") blackGraveyard_.columnStep.y = std::stod(value);
            else if (key == "black_graveyard_row_x") blackGraveyard_.rowStep.x = std::stod(value);
            else if (key == "black_graveyard_row_y") blackGraveyard_.rowStep.y = std::stod(value);
            else if (key == "black_graveyard_rows") blackGraveyard_.rows = static_cast<std::size_t>(std::stoul(value));
            else if (key == "black_graveyard_columns") blackGraveyard_.columns = static_cast<std::size_t>(std::stoul(value));
        } catch (const std::exception&) {
            board_.calibrated = false;
            whiteGraveyardConfigured_ = false;
            blackGraveyardConfigured_ = false;
            return false;
        }
    }

    const bool boardValid =
        !board_.calibrated ||
        (finite(board_.a1) &&
         std::isfinite(board_.squareSize) &&
         std::isfinite(board_.rotationRadians) &&
         board_.squareSize > 0.0);

    const bool whiteValid =
        !whiteGraveyardConfigured_ || validGrid(whiteGraveyard_);
    const bool blackValid =
        !blackGraveyardConfigured_ || validGrid(blackGraveyard_);

    if (!boardValid || !whiteValid || !blackValid) {
        board_.calibrated = false;
        whiteGraveyardConfigured_ = false;
        blackGraveyardConfigured_ = false;
        return false;
    }

    return board_.calibrated ||
           whiteGraveyardConfigured_ ||
           blackGraveyardConfigured_;
}

} // namespace ac::motion
