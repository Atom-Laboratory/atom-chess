"""RGB change evidence for a fixed, calibrated Graveyard inspection pose."""
import numpy as np
from PIL import Image, ImageDraw


class GraveyardEvidence:
    """Measure foreground changes against an empty-slot RGB calibration."""

    def __init__(self, empty_frame, polygon_px, *, channel_delta, min_fraction, max_drift_px):
        if not 0 < min_fraction < 1 or not 0 < channel_delta < 255:
            raise ValueError('Expected positive experimental thresholds')
        if not empty_frame.oriented or empty_frame.homography is None:
            raise ValueError('Empty calibration requires an oriented frame')
        if not np.isfinite(max_drift_px) or max_drift_px <= 0:
            raise ValueError('Expected a positive registration tolerance')
        empty_rgb = empty_frame.raw_rgb
        self.shape = empty_rgb.shape
        self.reference_id = empty_frame.reference_sha256
        self.camera_id = empty_frame.camera_id
        self.registration = empty_frame.homography
        self.max_drift_px = max_drift_px
        points = np.asarray(polygon_px, dtype=float)
        height, width = self.shape[:2]
        if (points.shape != (4, 2) or not np.isfinite(points).all()
                or (points < 0).any() or (points >= [width, height]).any()):
            raise ValueError('Slot polygon must be fully visible in the calibrated image')
        mask = Image.new('1', (width, height))
        ImageDraw.Draw(mask).polygon([tuple(point) for point in points], fill=1)
        self.mask = np.asarray(mask)
        if not self.mask.any():
            raise ValueError('Empty slot polygon')
        self.empty = empty_rgb[self.mask].astype(np.int16)
        self.points = np.column_stack((points, np.ones(len(points))))
        self.channel_delta = channel_delta
        self.min_fraction = min_fraction

    def observe(self, frame):
        if not frame.oriented or frame.homography is None or frame.raw_rgb.shape != self.shape:
            return None
        if (frame.reference_sha256 != self.reference_id or frame.camera_id != self.camera_id):
            return None
        mapping = np.linalg.solve(frame.homography, self.registration)
        projected = self.points @ mapping.T
        if (not np.isfinite(projected).all() or np.any(np.abs(projected[:, 2]) < 1e-12)):
            return None
        drift = np.linalg.norm(projected[:, :2]/projected[:, 2:] - self.points[:, :2], axis=1)
        if np.max(drift) > self.max_drift_px:
            return None
        change = np.abs(frame.raw_rgb[self.mask].astype(np.int16) - self.empty)
        return float(np.mean(np.max(change, axis=1) >= self.channel_delta))

    def summarize(self, frames):
        frames = tuple(frames)
        if len(frames) < 3 or any(a.sequence >= b.sequence for a, b in zip(frames, frames[1:])):
            raise ValueError('Expected at least three distinct ordered observations')
        scores = [self.observe(frame) for frame in frames]
        if None in scores:
            candidate = 'unknown'
        elif min(scores) >= self.min_fraction:
            candidate = 'foreground_candidate'
        elif max(scores) < self.min_fraction:
            candidate = 'background_candidate'
        else:
            candidate = 'unknown'
        return dict(candidate=candidate, changed_fraction=scores)
