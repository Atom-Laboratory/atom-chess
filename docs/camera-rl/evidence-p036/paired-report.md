# P036 paired saved-image comparison

Both methods process identical file bytes. Geometry uses the same
oracle D4 alignment. Orientation and named addressing are separate.
A rejected frame has unknown geometry and stays in denominators.

| Method | Accepted / total | Geometry correct / all squares | Named correct | Named unknown | Mean process ms |
|---|---:|---:|---:|---:|---:|
| checker | 11/27 | 704/1728 | 0 | 1728 | 716.91 |
| aruco | 24/27 | 1536/1728 | 1536 | 192 | 131.19 |

Geometry errors for accepted frames, rejection warnings, input identities,
source hashes, overlays and timing are in metrics.json and manifest.json.
Latency includes process startup and export. These static captures are
one experimental sweep, without independent statistical repetitions.
Mechanical acceptance thresholds, false-acceptance labels, physical grasp
error, CPU usage and piece localization are unavailable in this scope.
