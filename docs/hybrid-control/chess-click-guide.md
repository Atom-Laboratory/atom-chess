# Chess click integration

Build on Linux or WSL from the repository root:

    cmake -S . -B build/chess-ui -DACCHESS_BUILD_VIEWER=OFF
    cmake --build build/chess-ui --target chess_move_request -j 4

The Windows console invokes the compiled Linux bridge with WSL Ubuntu.
ATOM_CHESS_BRIDGE can point to a native executable instead. Click a piece of the
side to move, then the destination. The console submits immediately. Selecting
another friendly piece changes the source. Chess Core validates and TaskPlanner
orders captures or king/rook transfers. The board FEN is compared with confirmed
physical occupancy. Successful physical completion advances the game history.
Reset starts a new game. Manual changes or failed partial execution require
reconciliation. Promotion requires replacement support and is rejected.

Tests with the real bridge passed for illegal movement rejection, capture order
and castling decomposition. A complete E2-E3 click test in the populated current
scene was correctly blocked by a finger hull/adjacent D2 pawn collision at about
3.5 mm penetration. No move was committed. Capture decomposition is operational,
but complete capture manipulation in this collider configuration is unqualified.

Open virtual RGB camera displays the physical scene from above at 5 Hz.
Rendering was verified at 640x480. It is a preview input. acvision ingestion,
vision-based feedback, camera calibration and RL are still pending. Autonomous
execution is currently synchronous, so camera preview refreshes between tasks.
