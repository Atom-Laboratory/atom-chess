# P033 geometry validation

2026-11-06. Replaces largest-rectangle fallback with mandatory chess-pattern
support and a projective fit using all 49 internal corners. The outer boundary
is extrapolated at grid coordinates 0 and 8, not with a 0.8 image-vector multiplier.
No chess orientation or reliable occupancy is inferred from this fit.

Native regression: 4/4 CTest executables pass, including the new synthetic
perspective fixture at all four 90-degree rotations (outer corner error <2 pixels,
a raster-test tolerance only), direct-class parity and rectangle rejection.
Python integration tests also cover rectangle/sheet rejection rather than merely
labeling their false detections. See the run result for exact totals.

The unchanged three-view MuJoCo scene now returns no detection at -35 and -55
instead of mistaking the graveyard for the board. At -45 it assigns 64/64 centers
correctly with mean nominal-equivalent error 1.75 mm and p95 3.19 mm. These are
simulation diagnostics with oracle D4 alignment, not calibrated physical accuracy
or orientation. Detection coverage is 1/3 on this small scene set.

The strict detector intentionally loses rectangle-only detections under occlusion.
All candidate occupancy remains unknown; no cached homography is silently reused.
Next validation must measure viewpoint sensitivity and occupancy/color errors.
Training remains gated by those results and the missing verified manipulation
baseline. P032 evidence is preserved as the before-change baseline.

Python integration result: 15 passed in 4.16 seconds.

## Viewpoint and classification sweep

The follow-up evaluator sweeps provisional azimuths 265/270/275 degrees against
-35/-45/-55 elevation. These ±5-degree changes are diagnostic hypotheses, not
measured mounting tolerances. Run using the existing validation command plus
`--azimuths 265 270 275`; always choose a new output directory.

Detection succeeded in only 2/9 views:
- 265/-55: 64/64 center assignments; mean nominal error 1.82 mm, p95 2.92 mm;
  32 empty, 16 white and 16 black candidates all match the initial scene.
- 270/-45: 64/64 center assignments; mean nominal error 1.75 mm, p95 3.19 mm;
  all 32 occupied colors correct, but eight empty cells falsely classified occupied
  (four white, four black). Only 56/64 complete cell labels are correct.
- The remaining seven views return unknown/no detection, not an invented frame.

All comparisons use best D4 oracle alignment in the evaluator only. This is not
visual orientation validation. Candidate confusion is separate from confirmed
occupancy, which remains unknown. The scene is the initial arrangement; truth
labels come from initial_square metadata and are valid only for this static test.
No simulator state enters the native executable. A new test verifies confusion
counts without modifying the observation; final Python result: 16 passed in 4.21s.

Evidence: [viewpoint report](evidence-p033/viewpoint-report.json). Original captures
and diagnostic outputs remain in `simulation/mujoco/examples/validate_native_perception/runs/p033-viewpoint-sweep-20261106`.

## Remaining phases and stopping condition

- A audit and B1 bridge: complete for the documented offline scope.
- B2 geometry: projective fitting and rectangle rejection implemented/tested;
  occupied-board viewpoint robustness, orientation and reliable occupancy remain
  unvalidated. The 2/9 detection coverage is an explicit failed validation gate.
- C camera-based environment: not implemented; requires a dependable perception
  and freshness/occlusion contract. Returning unknown is deliberate, not success.
- D conventional visually verified full manipulation: not qualified; lacks visual
  gripper/height verification, calibrated metric frames and full collision evidence.
- E/F new RL training/comparison: not started because B2/D gates are unmet.

The next architectural dependency is an image-observable persistent board reference
(e.g. identifiable border fiducials or explicit setup calibration with verified
fixed camera/board and drift/loss detection). A cached homography must not silently
remain valid after camera/board motion. Real physical board dimensions, assembly,
reference placement and camera calibration are still missing. No fabricated marker
mount or simulator-derived calibration has been substituted. In accordance with
the redesign's stop-on-blocker requirement, this run stops at this measured gate,
not at a claim that all later phases are complete.
