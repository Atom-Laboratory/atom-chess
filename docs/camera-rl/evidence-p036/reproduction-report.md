# P036 historical reproduction report

| Protocol | Historical accepted | Current accepted | Rejected | Equal metric records | Identical PNGs |
|---|---:|---:|---:|---:|---:|
| p033 | 2/9 | 2/9 | 7 | 9/9 | 6/9 |
| p034 | 24/27 | 24/27 | 3 | 27/27 | 5/27 |

Protected files checked: 232.
Changed protected files: 0.

The JSON report records frame identities, pixel differences, overlays,
warnings, source/runtime identities and archived/reproduced metrics.
PNG identity differs for some renders, with a maximum observed channel
difference of 1.
The underlying cause of these rendering differences has not been isolated.
The executable has evolved since the historical experiments.
Model and layout identities are compared explicitly in the JSON.
Capture-script latency was unmeasured historically and remains unavailable.
Paired reprocessing latency is reported separately.
P033 geometry uses oracle D4 alignment. P034 named addressing uses the
configured marker orientation. Historical aggregates have different camera
distance and resolution, so causal method comparisons use the paired study.
