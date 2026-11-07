# Artifact migration status

102 existing experiment directories were transferred to their content owners.
The first 94 directories contain 3,707 files verified against the original
SHA-256 inventory. Eight additional directories were moved and verified
individually. 126 loose JSON reports were migrated with hash verification,
and 12 process logs were placed under their originating training run.

directory-migration.json, remaining-migration.json, loose-files-plan.json and
log-migration.json record original and destination locations.
Old directory junctions preserve paths embedded in immutable historical data.
Current code and documentation use the new physical destinations.

Unclassified empty directories, four old PPM previews, two arena process logs
and a few standalone calibration records remain preserved in runs pending
verified ownership. The old runs root therefore remains a compatibility area.
No checkpoint was deleted or isolated from its experiment metadata.

The full regression suite reported 93 passed, 52 skipped and one failure.
test_physical_capture_removes_before_attacker also failed in isolation with
GRIP_LOST_DURING_TRANSPORTING. Physics was not modified to hide this failure.
Fourteen current entry points loaded successfully with --help.

The wrist remains supported by manual control. Existing automatic trajectories
and P038 policies retain their five-actuator contract.
