"""Register visible pieces in marker-rectified board coordinates."""
import hashlib
import json
import numpy as np


def board_reference_shift(frame, planned_homography, pitch):
    """Maximum rectified board-corner displacement in metres."""
    height, width = frame.rectified_rgb.shape[:2]
    corners = np.array([[0., width, width, 0.], [0., 0., height, height], [1., 1., 1., 1.]])
    mapped = frame.homography@np.linalg.solve(planned_homography, corners)
    with np.errstate(divide='ignore', invalid='ignore'):
        delta = (mapped[:2]/mapped[2]-corners[:2])*np.array([8*pitch/width, 8*pitch/height])[:, None]
    return float(np.linalg.norm(delta, axis=0).max()) if np.isfinite(delta).all() else float('inf')


def registration_identity(scene):
    anchor = getattr(scene, 'registration', None)
    if anchor is None:
        return None
    frame = anchor['frame']
    digest = hashlib.sha256(frame.rectified_rgb.tobytes())
    digest.update(json.dumps(dict(offsets=anchor['offsets'], tolerance_m=anchor['tolerance_m'],
        homography=frame.homography.tolist(), camera_id=frame.camera_id,
        reference_sha256=frame.reference_sha256), sort_keys=True, allow_nan=False).encode())
    return digest.hexdigest()


def scene_square_offsets(scene, observed, occupied):
    """Camera-only scene estimates, optionally relative to an anchored real image."""
    anchor = getattr(scene, 'registration', None)
    if anchor is None:
        return square_offsets(scene.empty_reference, scene.centered_reference, observed, occupied, scene.pitch)
    reference = anchor['frame']
    if not _compatible(reference, observed):
        return {}
    try:
        shift = board_reference_shift(observed, reference.homography, scene.pitch)
    except (ValueError, TypeError, np.linalg.LinAlgError):
        return {}
    if shift > anchor['tolerance_m']:
        return {}
    offsets = square_offsets(scene.empty_reference, reference, observed, occupied, scene.pitch)
    return {square: (np.asarray(anchor['offsets'][square])+delta).tolist()
            for square, delta in offsets.items() if square in anchor['offsets']}


def _compatible(reference, observed):
    return (reference.oriented and observed.oriented
            and bool(reference.reference_sha256)
            and reference.reference_sha256 == observed.reference_sha256
            and reference.camera_id == observed.camera_id
            and reference.rectified_rgb.shape == observed.rectified_rgb.shape)


def _shift(template, observed, radius=12):
    """Return the best small translation of a foreground silhouette in pixels."""
    if min(template.sum(), observed.sum()) < 30:
        return None
    # Search in a zero-padded image to avoid wrapping across square boundaries.
    shape = tuple(2*n for n in template.shape)
    cross = np.fft.irfft2(
        np.fft.rfft2(observed, s=shape, axes=(0, 1))
        * np.fft.rfft2(template, s=shape, axes=(0, 1)).conj(),
        s=shape, axes=(0, 1))
    offsets = np.arange(-radius, radius+1)
    intersections = np.rint(cross[np.ix_(offsets, offsets)])
    scores = intersections/(template.sum()+observed.sum()-intersections)
    y, x = np.unravel_index(np.argmax(scores), scores.shape)
    if scores[y, x] < .55 or not (0 < x < 2*radius and 0 < y < 2*radius):
        return None
    # Broad, ambiguous matches are not position evidence.
    distant = (offsets[:, None]-offsets[y])**2+(offsets[None, :]-offsets[x])**2 > 9
    if scores[y, x]-scores[distant].max() < .015:
        return None
    return np.array([offsets[x], offsets[y]])


def square_offsets(empty, reference, observed, occupied, square_size_m):
    """Return only visually supported XY offsets relative to the reference RGB."""
    if not _compatible(empty, reference) or not _compatible(reference, observed):
        return {}
    background = empty.rectified_rgb.astype(np.int16)
    contrast = [np.max(abs(frame.rectified_rgb.astype(np.int16)-background), axis=2)
                for frame in (reference, observed)]
    height, width = background.shape[:2]
    cell_h, cell_w = height//8, width//8
    scale = np.array([square_size_m/cell_w, -square_size_m/cell_h])
    estimates = {}
    for square in occupied:
        row, column = 8-int(square[1]), ord(square[0])-ord('a')
        crop = np.s_[row*cell_h+8:(row+1)*cell_h-8, column*cell_w+8:(column+1)*cell_w-8]
        # Low contrast keeps pale pieces on light squares visible. A stronger
        # threshold can recover edges when shadows obscure the full silhouette.
        shift = _shift(*(image[crop] >= 9 for image in contrast))
        if shift is None:
            shift = _shift(*(image[crop] >= 40 for image in contrast))
        if shift is not None:
            estimates[square] = (shift*scale).tolist()
    return estimates


def configuration_from_offsets(model, pieces, addresses, command, offsets, occupied):
    """Static calibrated scene plus RGB XY offsets, with no live object poses."""
    if set(offsets) != set(occupied):
        raise ValueError('Incomplete RGB localization of the expected occupied squares')
    configuration = model.qpos0.copy()
    for piece in pieces:
        body = model.body(piece['name']).id
        address = model.jnt_qposadr[model.body_jntadr[body]]
        configuration[address:address+2] += offsets[piece['initial_square']]
    configuration[addresses] = command
    return configuration
