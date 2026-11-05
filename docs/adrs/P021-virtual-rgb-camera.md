# P021 — Virtual RGB camera input

Expose a fixed overhead RGB camera in a separate panel at 5 Hz using the existing
MuJoCo renderer. Its pose is an experimental view of the configured board. The
RGB image is available independently from logical and confirmed physical state.
The current panel is a preview. acvision ingestion, calibrated orientation,
uncertainty and camera-based execution confirmation remain pending.
The image contains only the physical model, without selection overlays.
The camera was validated at 640x480 with nonuniform RGB output.
