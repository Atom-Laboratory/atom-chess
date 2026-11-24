# Fixed H-file camera and reference markers

The camera settings are defined in src/atom_mujoco/virtual_camera.py.
h-file-layout.json is the default ArUco layout for new reference scenes and
camera fixtures. A run must generate its reference-scene.xml with the same
layout used by native perception. Existing generated scenes embed the old
marker positions and must be regenerated to adopt this layout.

Use --layout for an experimental marker layout and --camera-config for a
camera override. Preserve both files with the run. See
[ADR S012](../../../docs/adrs/S012-h-file-marker-visibility.md) for coordinates,
orientation, experimental status and trajectory validation.

The marker strip occupies space beyond the H-file edge. Hardware installation
requires measuring these positions relative to the actual board and printing
the markers at the specified dimensions. A changed board size requires a
matching measured layout.

A successful static calibration must be followed by a full moving-arm baseline.
The old arrangement passed static calibration and failed during approach.
