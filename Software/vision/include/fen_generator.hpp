
#ifndef AC_FEN_GENERATOR_HPP
#define AC_FEN_GENERATOR_HPP

#include <array>
#include <string>
#include "piece_detector.hpp"

namespace ac
{

class FenGenerator
{
public:
    static std::string generate(
        const std::array<std::array<CellState,8>,8>& board
    );
};

}

#endif
