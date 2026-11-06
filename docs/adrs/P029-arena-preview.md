# P029 — Shared 3D arena preview

Render repeated ATOM stations in one MuJoCo viewer for layout inspection.
Share the arm meshes and simplify piece geometry for the wide view. Keep
this scene static while training is stopped. A future live arena can mirror
independent simulator states into these stations. Policy ownership and
physics isolation belong to the training backend.
