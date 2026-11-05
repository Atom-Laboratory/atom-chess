#include <iostream>
#include <stdexcept>
#include <string>
#include "board/move_validator.hpp"
#include "board/move_applier.hpp"
#include "fen_generator/fen_generator.hpp"
#include "motion/task_planner.hpp"

std::string square(ac::chess::Square s) {
    return {static_cast<char>('a'+s.col),static_cast<char>('8'-s.row)};
}
int main(int argc,char** argv) {
    using namespace ac;
    try {
        if(argc<2) throw std::invalid_argument("A proposed UCI move is required");
        chess::Board board;
        for(int i=1;i<argc-1;++i) {
            auto move=chess::MoveValidator::validateUci(board,argv[i]);
            if(!move) throw std::invalid_argument("Invalid prior move");
            chess::MoveApplier::apply(board,*move);
        }
        auto move=chess::MoveValidator::validateUci(board,argv[argc-1]);
        if(!move) throw std::invalid_argument("Illegal move for current position");
        if(move->promotion!=chess::PieceType::None) throw std::invalid_argument("Physical promotion unsupported");
        motion::CoordinateMapper mapper("");
        mapper.calibrateBoard({0,0},{280,0});
        const motion::GridGeometry grid{{0,0},{40,0},{0,40},2,8};
        mapper.setGraveyardGeometry(motion::GraveyardSide::WHITE,grid);
        mapper.setGraveyardGeometry(motion::GraveyardSide::BLACK,grid);
        motion::GraveyardAllocator allocator(mapper);
        motion::TaskPlanner planner(mapper,allocator);
        auto tasks=planner.planTasks(board,*move);
        std::cout << "{\"fen\":\"" << chess::FenGenerator::generate(board) << "\",\"steps\":[";
        bool first=true;
        for(const auto& task:tasks) {
            if(!first) std::cout << ',';
            first=false;
            std::cout << "{\"source\":\"" << square(*task.boardSource) << "\",\"target\":\"";
            if(task.type==motion::PhysicalTaskType::RemoveCapturedPiece) std::cout << "home";
            else std::cout << square(*task.boardTarget);
            std::cout << "\"}";
        }
        std::cout << "]}\n";
    } catch(const std::exception& e) {
        std::cerr << e.what() << '\n'; return 1;
    }
}
