# ATOM Chess

ATOM Chess is a research and development project focused on building an autonomous robotic chess system capable of perceiving a physical chessboard, analyzing the current game state, selecting a move, and physically executing it.

The project combines computer vision, chess programming, artificial intelligence, robotics, motion planning, and embedded systems into a single autonomous platform.

## Project Goals

The primary objective of ATOM Chess is to develop a self-contained robotic system capable of:

* Perceiving the physical chessboard through a camera.
* Determining the current board state.
* Detecting changes caused by human moves.
* Representing the position computationally.
* Generating a valid FEN representation.
* Querying a chess engine for the next move.
* Planning the required robotic motion.
* Executing the move on the physical board.
* Verifying the resulting board state.
* Recovering from unexpected situations.

The system is designed with modularity and hardware/software separation in mind, allowing individual subsystems to be developed, tested, and replaced independently.

## Project Leadership

ATOM Chess was conceived and initiated by Enzo Ribas, who leads the project’s technical and product development. He is responsible for defining the system architecture, coordinating the multidisciplinary development effort, and contributing across software engineering, computer vision, robotics, electronics, and mechanical systems. The project reflects his approach to integrating these disciplines into a cohesive autonomous platform. For more information about his work and professional background, visit his [LinkedIn profile](https://www.linkedin.com/in/oenzoribas/).

## System Architecture

ATOM Chess is organized into four primary subsystems:

### Vision

The vision subsystem is responsible for converting camera data into structured information about the chessboard.

Its responsibilities include:

* Camera acquisition.
* Camera calibration.
* Chessboard detection.
* Perspective correction.
* Homography computation.
* Board coordinate mapping.
* Cell extraction.
* Piece occupancy detection.
* Board-state reconstruction.
* Move detection.

The vision pipeline is designed to provide the chess core with a representation of the physical board rather than exposing computer-vision-specific details to the rest of the system.

### Chess Core

The chess core contains the domain model and game-state logic.

It is responsible for:

* Board representation.
* Piece representation.
* Square representation.
* Move representation.
* Board state comparison.
* FEN generation.
* Game-state management.
* Move validation.
* Chess-engine integration.

The core is intentionally independent of the physical robot and computer-vision implementation.

### Engine and Planning

The planning layer connects the chess domain to the robotic system.

It is responsible for:

* Requesting moves from the chess engine.
* Translating chess moves into physical actions.
* Selecting the required sequence of robotic operations.
* Generating trajectories.
* Computing the required robot configuration.
* Handling execution constraints.

The chess engine is treated as a decision component rather than as part of the board representation itself.

### Motion and Control

The motion subsystem is responsible for physically executing planned operations.

Its responsibilities include:

* Trajectory interpolation.
* Motion profiling.
* Inverse kinematics.
* Motor control.
* Communication with the motion controller.
* Execution of robotic commands.
* Hardware-level safety and error handling.

The current architecture separates high-level planning from low-level motor control, allowing computationally intensive logic to remain outside the microcontroller.

## Technology Stack

The project uses technologies including:

* C++
* Python
* OpenCV
* CMake
* Ninja
* GoogleTest
* Stockfish
* ESP32
* Embedded C/C++
* Computer vision
* Robotics and inverse kinematics

Additional technologies may be introduced as individual subsystems evolve.

## Build

The project uses CMake as its build-system generator.

A typical build configuration is:

```bash
cmake -S . -B build
cmake --build build
```

Tests can be executed through the configured test target or CTest:

```bash
ctest --test-dir build
```

The exact build configuration may vary depending on the target platform and enabled components.

## Project Status

ATOM Chess is under active development.

Current development is focused on establishing a robust software foundation before integrating the complete perception, chess-engine, planning, and robotic-control pipeline.

The architecture is intentionally evolving as the individual subsystems are validated experimentally.

## Research

ATOM Chess is also intended as a research platform. Its modular architecture enables experimentation in areas including:

* Computer vision for structured environments.
* Chess position recognition.
* Automated move detection.
* Chess position representation.
* Chess-engine integration.
* Robotic manipulation.
* Motion planning.
* Inverse kinematics.
* Autonomous system architectures.
* Human-robot interaction.

The platform is designed so that individual components can be benchmarked and replaced without requiring a complete redesign of the system.

## License

This project is currently under development. Licensing information will be added when the project's distribution model is finalized.

## Contributors

ATOM Chess is developed as part of the ATOM Project by a multidisciplinary team working across software engineering, computer vision, robotics, electronics, mechanical engineering, and research.

Contributions should follow the project's architectural conventions, testing requirements, coding standards, and commit guidelines.
