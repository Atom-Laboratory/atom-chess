"""Task-conditioned actor inputs built exclusively from RGB and host command history."""
from dataclasses import dataclass
import math
import time

import numpy as np
from PIL import Image

from .native_vision import CameraObservation, _readonly


PHASES = ('OBSERVE', 'APPROACH', 'GRASP', 'LIFT', 'TRANSPORT', 'PLACE', 'RELEASE', 'RETREAT')


@dataclass(frozen=True)
class PolicyObservation:
    frame_sequence: int
    camera_id: str
    image_chw: np.ndarray
    task: np.ndarray
    previous_action: np.ndarray
    commanded_joints: np.ndarray
    phase_index: int
    native_source_sha256: str
    reference_sha256: str

    def features(self):
        return dict(image=self.image_chw.copy(), task=self.task.copy(),
                    previous_action=self.previous_action.copy(),
                    commanded_joints=self.commanded_joints.copy(),
                    phase=np.array([self.phase_index], dtype=np.int64))


def _square(square):
    if (not isinstance(square, str) or len(square) != 2
            or square[0] not in 'abcdefgh' or square[1] not in '12345678'):
        raise ValueError('Expected lowercase algebraic square')
    return [ord(square[0])-ord('a'), 8-int(square[1])]


def policy_observation(frame, *, source, target, previous_action, commanded_joints,
                       phase='OBSERVE', now_s=None, max_age_s=.25):
    if not isinstance(frame, CameraObservation):
        raise TypeError('CameraObservation required')
    now = time.monotonic() if now_s is None else now_s
    if not all(isinstance(value, (float, int)) and math.isfinite(value)
               for value in (now, max_age_s)) or max_age_s <= 0:
        raise ValueError('Finite clock and positive age budget required')
    if now < frame.captured_at_s or now-frame.captured_at_s > max_age_s:
        raise ValueError('STALE_OR_FUTURE_FRAME')
    if frame.homography is None or not frame.oriented or not frame.reference_sha256:
        raise ValueError('BOARD_REFERENCE_UNAVAILABLE')
    if phase not in PHASES or source == target:
        raise ValueError('Expected distinct task squares and supported phase')
    task = np.array(_square(source)+_square(target), dtype=np.float32)/7
    action = np.asarray(previous_action, dtype=np.float32)
    command = np.asarray(commanded_joints, dtype=np.float32)
    if (action.shape != (4,) or command.shape != (5,) or not np.isfinite(action).all()
            or not np.isfinite(command).all() or np.any(np.abs(action) > 1)):
        raise ValueError('Expected normalized prior action and five finite commanded joints')
    image = np.array(Image.fromarray(frame.rectified_rgb).resize(
        (96, 96), Image.Resampling.BILINEAR)).transpose(2, 0, 1)
    return PolicyObservation(frame.sequence, frame.camera_id, _readonly(image),
                             _readonly(task), _readonly(action), _readonly(command),
                             PHASES.index(phase), frame.native_source_sha256, frame.reference_sha256)
