#pragma once
namespace ac::chess {
struct Square {
    int row{-1};
    int col{-1};

    bool operator==(const Square& other) const;

    bool operator!=(const Square& other) const;
};
}
