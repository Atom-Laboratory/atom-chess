#pragma once
namespace ac::chess {
struct Square {
    int row;
    int col;

    bool operator==(const Square& other) const;

    bool operator!=(const Square& other) const;
};
}
