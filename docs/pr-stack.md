# Pull request stack

Updated 2026-11-20. Parent branches are synchronized before their children.

```text
main
  #174 ros2_simulation
    #175 codex/atom-rl-training-diagnostics
      #177 codex/engineering-knowledge-assistant
      #180 codex/planner-started-reach (draft)
    #179 opencode/hardware-workspace (draft)
```

Hardware and RL are siblings: neither requires the other's changes. Merge #174
first, then #175 and #179 independently, then #177 and #180 independently after
#175. The knowledge assistant and planner-started reach are siblings. Retarget children
to the parent's target after merging and synchronize again before proceeding.
Keep the root PR blocked until its CI failures are resolved; a conflict-free
stack does not qualify hardware execution or manipulation success.

For every update: fetch/prune, inspect open PR bases/heads, merge the updated
parent into its child without rewriting published commits, resolve conflicts,
run affected checks, push and verify GitHub mergeability. Preserve focused PR
diffs. Follow the stack convention in the repository AGENTS.md.
