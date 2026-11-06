"""Camera evidence of changes in configured neighboring board cells."""
import numpy as np


class NeighborEvidence:
    def __init__(self, frame, squares, *, channel_delta=35, max_changed_fraction=.03):
        if not frame.oriented or frame.homography is None:
            raise ValueError('Neighbor reference requires an oriented camera frame')
        self.reference = frame.rectified_rgb.astype(np.int16).copy()
        self.reference_id = frame.reference_sha256
        self.camera_id = frame.camera_id
        self.squares = tuple(squares)
        self.channel_delta = channel_delta
        self.limit = max_changed_fraction

    def observe(self, frame):
        if (not frame.oriented or frame.homography is None
                or frame.reference_sha256 != self.reference_id
                or frame.camera_id != self.camera_id):
            return None
        difference = np.max(abs(frame.rectified_rgb.astype(np.int16)-self.reference), axis=2)
        result = {}
        for square in self.squares:
            row, column = 8-int(square[1]), ord(square[0])-97
            crop = difference[row*100+8:(row+1)*100-8, column*100+8:(column+1)*100-8]
            result[square] = float(np.mean(crop >= self.channel_delta))
        return result
