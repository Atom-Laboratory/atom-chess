# S028 — Prune collision pairs with conservative interval certificates

## Context

Autonomous manipulation validates many short joint-space segments. The
existing recursive sweep repeatedly queries pairs that have already been
certified clear over the parent interval. Distance evaluation and repeated
full forward dynamics contribute significant collection cost.

## Decision

Add an opt-in pruning path. At each interval midpoint, use each bounded
geometry's enclosing sphere and its conservative motion bound to eliminate
pairs proven clear throughout that interval. Carry only unresolved pairs
into descendant intervals. Keep planes and heightfields unbounded. Nonfinite
values remain candidates for a failing distance query.

Refresh kinematics for geometry queries in this mode. Retain the original
full-forward path as the default comparison. Preserve the configured
clearance, subdivision limit, sample budget and fail-closed behavior for
unresolved intervals. Carried-object configuration and additional motion
coefficients must be passed through both paths.

## Alternatives

Lower sample counts or omitted gripper geometry would change the physical
admission criterion. Reusing a sampled clear pose alone would provide no
certificate over the complete trajectory. Parent interval certificates
provide the scope needed to reuse clearance across their subintervals.

## Consequences and validation

Compare clear, colliding and unresolved outcomes between the original and
optimized algorithms. Test infinite planes whose arbitrary origin lies far
from the moving geometry. The native fixture regression also compares the
blocked full-gripper path and verifies that rejected execution leaves live
state unchanged. These tests qualify the implementation under its model
assumptions. Experimental geometry and dynamic execution retain their
independent supervision requirements.
