# S043 — Anchor local tracking to a validated real RGB observation

Status: experimental. Date: 2026-11-20.

## Context

S042 rejected the known queen-D1 continuation and selected a nominally clear
alternative. Actual arrival then failed centered-template localization. The
centered template is a synthetic calibration image; a real park frame already
contains a visually localized piece and the actual appearance for that episode.

## Decision

Opt in to a real RGB registration anchor at reset. Localize all occupied squares
against the existing centered calibration, then bind those estimated offsets to
that actual park image. Later estimates compose the anchored offsets with RGB
translations measured from the anchor. The anchor contains no measured body or
joint coordinates and is not refreshed from privileged simulation state.

Use one scene-localization helper for planning, execution, handoff and actor
features. Reject missing/ambiguous pieces, camera/reference mismatches and marker
homography drift. Do not fall back to a remembered coordinate when tracking fails.
Bind the anchor image/offset identity to the signed plan and validate it again
before issuing motion. Keep silhouette confidence thresholds unchanged.

## Alternatives and consequences

Disabling arrival checks or filling in a simulator position would hide the failure.
Re-rendering at the known actual pose violates the observation boundary. An
anchored real image avoids both, but does not guarantee robust perception under
all occlusions or illumination. Reference drift still fails closed. The board
epoch must be renewed after verified logical/physical changes in a real game;
this experiment renews it per reset. No depth or extra sensor is introduced.
