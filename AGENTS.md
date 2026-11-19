# Repository working conventions

Maintain developer documentation in English.

Every new runnable example must have an entry in its nearest README. Include
its purpose, prerequisites, commands from the repository root, expected outputs,
test commands and material limitations. Update the module README whenever its
default behavior or supported workflow changes.

Keep current instructions distinct from historical profile notes. In MuJoCo,
distinguish the interactive Playground, legacy v3 pixel training and the P038
native camera-guided residual environment.

Use fresh output directories for experiments and checkpoints. Record source,
configuration and model identities. Preserve earlier results and CAD assets.

Review changes and run relevant tests before committing. Separate independent
modules and architectural increments into coherent commits.

Before creating or updating a PR, inspect all open PRs and their base/head
branches. Stack dependent changes on the nearest prerequisite PR; keep independent
changes as siblings. Record parent/child links and merge order in PR descriptions.
Synchronize parents before children, resolve conflicts locally, run relevant
checks, and verify remote mergeability after pushing. Prefer ordinary merge
commits over rewriting published history. After a parent is merged, retarget
and synchronize its children before merging them. Never equate mergeability
with passing CI, and never merge a PR solely to organize the stack.
