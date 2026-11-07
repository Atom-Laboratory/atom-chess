"""RGB silhouette agreement with an upright camera calibration."""
import numpy as np


def dilate(mask):
    padded = np.pad(mask, 1)
    height, width = mask.shape
    return np.logical_or.reduce([padded[y:y+height, x:x+width]
                                 for y in range(3) for x in range(3)])


def foreground_mask(image, empty, delta):
    raw = np.max(abs(image.astype(np.int16)-empty), axis=2) >= delta
    remaining = set(map(tuple, np.argwhere(raw)))
    cleaned = np.zeros_like(raw)
    while remaining:
        first = remaining.pop()
        component = [first]
        pending = [first]
        while pending:
            y, x = pending.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    point = (y+dy, x+dx)
                    if point in remaining:
                        remaining.remove(point)
                        component.append(point)
                        pending.append(point)
        if len(component) >= 4:
            ys, xs = zip(*component)
            cleaned[ys, xs] = True
    return dilate(cleaned)


class PieceAppearance:
    def __init__(self, empty, upright, square, *, channel_delta=35, minimum_iou=.65, placement_tolerance_px=8):
        row, column = 8-int(square[1]), ord(square[0])-97
        self.crop = np.s_[row*100+8:(row+1)*100-8, column*100+8:(column+1)*100-8]
        self.empty = empty[self.crop].astype(np.int16)
        images = upright if isinstance(upright, (list, tuple)) else [upright]
        self.masks = [foreground_mask(image[self.crop], self.empty, channel_delta)
                      for image in images]
        self.mask = self.masks[0]
        if not self.mask.any():
            raise ValueError('Upright calibration has no visible target silhouette')
        self.delta = channel_delta
        self.minimum_iou = minimum_iou
        self.tolerance = placement_tolerance_px

    def score(self, image):
        mask = foreground_mask(image[self.crop], self.empty, self.delta)
        radius = self.tolerance
        padded = np.pad(mask, radius)
        height, width = mask.shape
        best = 0.
        for dy in range(-radius, radius+1, 2):
            for dx in range(-radius, radius+1, 2):
                shifted = padded[radius+dy:radius+dy+height, radius+dx:radius+dx+width]
                for reference in self.masks:
                    union = np.count_nonzero(shifted | reference)
                    if union:
                        best = max(best, float(np.count_nonzero(shifted & reference)/union))
        return best
