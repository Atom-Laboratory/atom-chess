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
