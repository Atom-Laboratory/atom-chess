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
