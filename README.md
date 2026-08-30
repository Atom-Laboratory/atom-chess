# ATOM Chess

ATOM Chess is a research and development project focused on building an autonomous robotic chess system capable of perceiving a physical chessboard, analyzing the current game state, selecting a move, and physically executing it.

The project combines computer vision, chess programming, artificial intelligence, robotics, motion planning, and embedded systems into a single autonomous platform.

## ATOM Laboratory

ATOM Chess is part of **ATOM Laboratory**, a broader research and development initiative focused on the integration of robotics, computer vision, artificial intelligence, software engineering, electronics, and mechanical engineering.

ATOM Laboratory provides the broader research context in which ATOM Chess is developed. Other projects may be developed independently within the laboratory, with their own technical objectives, architectures, and licensing models.

ATOM Chess is one of the laboratory's open-source software projects, while its physical hardware remains proprietary unless explicitly released under a separate hardware license.


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

ATOM Chess was conceived and initiated by **Enzo Ribas**, who leads the project’s technical and product development. He is responsible for defining the system architecture, coordinating the multidisciplinary development effort, and contributing across software engineering, computer vision, robotics, electronics, and mechanical systems.

For more information about his work and professional background, visit his [Enzo's LinkedIn profile](https://www.linkedin.com/in/oenzoribas/).

## System Architecture

ATOM Chess is organized into four primary subsystems:

### Vision

The vision subsystem is responsible for converting camera data into structured information about the chessboard.

### Chess Core

The chess core contains the domain model and game-state logic.

The core is intentionally independent of the physical robot and computer-vision implementation.

### Engine and Planning

The planning layer connects the chess domain to the robotic system.

The chess engine is treated as a decision component rather than as part of the board representation itself.

### Motion and Control

The motion subsystem is responsible for physically executing planned operations.

The current architecture separates high-level planning from low-level motor control, allowing computationally intensive logic to remain outside the microcontroller.

## Build

The project uses CMake as its build-system generator.

The supported development environment is Linux.

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

## Contributing

ATOM Chess is developed as a collaborative, multidisciplinary project involving software engineers, computer scientists, researchers, and contributors working across computer vision, chess programming, robotics, electronics, mechanical engineering, and related fields.



Contributions may include:

* Bug fixes.
* New features.
* Tests.
* Documentation.
* Refactoring.
* Performance improvements.
* Research implementations.
* Computer vision improvements.
* Chess algorithms.
* Robotics and motion-planning algorithms.

Pull requests should be focused, tested, and clearly describe the motivation, implementation, and testing performed.

All contributions are expected to follow the project's contribution guidelines, coding standards, testing requirements, and architectural conventions.

For information about contributing, see [`CONTRIBUTING.md`](.github/CONTRIBUTING.md).

Community members are also encouraged to review existing pull requests. Review guidelines and the community review template are available in [`.github/REVIEW_TEMPLATE.md`](.github/REVIEW_TEMPLATE.md).

## Licensing

ATOM Chess uses separate licensing for software and hardware.

### Software

The ATOM Chess software is released under the MIT License.

See [`LICENSE`](LICENSE) for the complete license text.

Unless explicitly stated otherwise, the MIT License applies to the software source code contained in this repository.

### Hardware

The ATOM Chess hardware is currently **not open source**.

Hardware designs are not licensed under the MIT License.

This includes, but is not limited to:

* Mechanical CAD files.
* Mechanical drawings.
* Electrical schematics.
* PCB designs.
* PCB layouts.
* Manufacturing files.
* Bills of materials.
* Assembly documentation.
* Manufacturing documentation.

Unless explicitly stated otherwise, no permission is granted to reproduce, manufacture, modify, distribute, or commercially exploit the ATOM Chess hardware designs.

See [`HARDWARE_LICENSE.md`](HARDWARE_LICENSE.md) for the current hardware licensing policy.

### Third-Party Materials

Third-party software, hardware, documentation, libraries, models, and other materials remain subject to their respective licenses.

The ATOM Chess MIT License does not supersede or replace the license of third-party materials.