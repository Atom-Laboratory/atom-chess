"""Pure visual and host-data interface for the autonomous actor."""
from collections import deque

import numpy as np
from PIL import Image


class VisualHistory:
    def __init__(self):
        self.images = deque(maxlen=2)
        self.commands = deque(maxlen=2)

    def clear(self):
        self.images.clear()
        self.commands.clear()

    def observe(self, frame, command, previous_action, source, target):
        valid = bool(frame.oriented and frame.homography is not None and frame.reference_sha256)
        image = (np.asarray(Image.fromarray(frame.rectified_rgb).resize((96, 96),
                 Image.Resampling.BILINEAR)).transpose(2, 0, 1).copy()
                 if valid else np.zeros((3, 96, 96), dtype=np.uint8))
        self.images.append(image)
        self.commands.append(np.asarray(command, dtype=np.float32).copy())
        if len(self.images) == 1:
            self.images.append(image.copy())
            self.commands.append(self.commands[-1].copy())
        task = [ord(source[0])-97, 8-int(source[1]), ord(target[0])-97, 8-int(target[1])]
        return dict(image=np.concatenate(self.images).copy(),
                    task=np.asarray(task, dtype=np.float32)/7,
                    commanded_joints=self.commands[-1].copy(),
                    command_history=np.concatenate(self.commands).copy(),
                    previous_action=np.asarray(previous_action, dtype=np.float32).copy(),
                    perception_valid=np.array([valid], dtype=np.float32))
