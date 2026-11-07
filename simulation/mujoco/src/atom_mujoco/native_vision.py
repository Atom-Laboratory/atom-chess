"""Persistent RGB-to-acvision boundary. The native context has no simulator access."""
import ctypes
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import threading
import time

import numpy as np


class _Frame(ctypes.Structure):
    _fields_ = [
        ('abi_version', ctypes.c_uint32), ('board_valid', ctypes.c_int32),
        ('oriented', ctypes.c_int32), ('has_foreground', ctypes.c_int32),
        ('homography', ctypes.c_double * 9), ('reference_residual', ctypes.c_double),
        ('candidates', ctypes.c_int32 * 64), ('center_valid', ctypes.c_int32 * 64),
        ('centers', ctypes.c_double * 128),
    ]


@dataclass(frozen=True)
class CameraObservation:
    sequence: int
    captured_at_s: float
    camera_id: str
    reference_sha256: str | None
    native_source_sha256: str
    raw_rgb: np.ndarray
    rectified_rgb: np.ndarray
    homography: np.ndarray | None
    oriented: bool
    candidates: np.ndarray
    foreground_centroids: np.ndarray | None
    reference_residual_px: float | None
    processing_ms: float


def _readonly(array):
    # Immutable byte backing prevents re-enabling NumPy's write flag.
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)


class NativeVision:
    def __init__(self, library, *, layout=None, camera_id='simulation-camera'):
        if not isinstance(camera_id, str) or not camera_id.strip():
            raise ValueError('A camera identity is required')
        library = Path(library).resolve(strict=True)
        self._lock = threading.Lock()
        self._dll_directory = os.add_dll_directory(str(library.parent)) if os.name == 'nt' else None
        self._native = ctypes.CDLL(str(library))
        lib = self._native
        pointer = ctypes.POINTER(ctypes.c_uint8)
        lib.acvision_runtime_version.restype = ctypes.c_uint32
        lib.acvision_frame_size.restype = ctypes.c_size_t
        lib.acvision_runtime_source.restype = ctypes.c_char_p
        lib.acvision_runtime_error.restype = ctypes.c_char_p
        lib.acvision_runtime_create.argtypes = [ctypes.c_char_p]
        lib.acvision_runtime_create.restype = ctypes.c_void_p
        lib.acvision_runtime_destroy.argtypes = [ctypes.c_void_p]
        lib.acvision_runtime_empty.argtypes = [
            ctypes.c_void_p, pointer, ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
        lib.acvision_runtime_empty.restype = ctypes.c_int
        lib.acvision_runtime_process.argtypes = [
            ctypes.c_void_p, pointer, ctypes.c_size_t, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(_Frame), pointer, ctypes.c_size_t]
        lib.acvision_runtime_process.restype = ctypes.c_int
        if lib.acvision_runtime_version() != 1 or lib.acvision_frame_size() != ctypes.sizeof(_Frame):
            raise ValueError('Incompatible native vision ABI')
        path = Path(layout).resolve(strict=True) if layout else None
        self.reference_sha256 = hashlib.sha256(path.read_bytes()).hexdigest() if path else None
        self._context = lib.acvision_runtime_create(str(path).encode('utf-8') if path else None)
        if not self._context:
            raise ValueError(self._error())
        self.camera_id = camera_id
        self.source_sha256 = lib.acvision_runtime_source().decode('ascii')
        self._sequence = 0

    def _error(self):
        return self._native.acvision_runtime_error().decode('utf-8', errors='replace')

    @staticmethod
    def _rgb(rgb):
        if (not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8 or rgb.ndim != 3
                or rgb.shape[2] != 3 or not rgb.flags.c_contiguous
                or not all(27 <= value <= 8192 for value in rgb.shape[:2])):
            raise ValueError('Expected contiguous uint8 RGB HxWx3, dimensions 27..8192')
        return rgb.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))

    def set_empty(self, rgb):
        pointer = self._rgb(rgb)
        with self._lock:
            if not self._context:
                raise RuntimeError('Native vision is closed')
            status = self._native.acvision_runtime_empty(
                self._context, pointer, rgb.nbytes, rgb.shape[1], rgb.shape[0])
            if status < 0:
                raise ValueError(self._error())
            return status == 1

    def observe(self, rgb, *, captured_at_s=None):
        pointer = self._rgb(rgb)
        captured_at = time.monotonic() if captured_at_s is None else captured_at_s
        if not isinstance(captured_at, (float, int)) or not np.isfinite(captured_at) or captured_at < 0:
            raise ValueError('Expected finite nonnegative capture time')
        rectified = np.zeros((800, 800, 3), dtype=np.uint8)
        output = _Frame()
        with self._lock:
            if not self._context:
                raise RuntimeError('Native vision is closed')
            begin = time.perf_counter()
            status = self._native.acvision_runtime_process(
                self._context, pointer, rgb.nbytes, rgb.shape[1], rgb.shape[0],
                ctypes.byref(output),
                rectified.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)), rectified.nbytes)
            elapsed = (time.perf_counter()-begin)*1000
            if status < 0:
                raise ValueError(self._error())
            self._sequence += 1
            sequence = self._sequence
        H = np.array(output.homography).reshape(3, 3) if output.board_valid else None
        candidates = np.array(output.candidates, dtype=np.int32).reshape(8, 8)
        centers = None
        if output.has_foreground:
            centers = np.array(output.centers).reshape(8, 8, 2)
            centers[np.array(output.center_valid).reshape(8, 8) == 0] = np.nan
        return CameraObservation(
            sequence, float(captured_at), self.camera_id, self.reference_sha256,
            self.source_sha256, _readonly(rgb), _readonly(rectified),
            _readonly(H) if H is not None else None, bool(output.oriented),
            _readonly(candidates), _readonly(centers) if centers is not None else None,
            float(output.reference_residual) if output.oriented else None, elapsed)

    def close(self):
        with self._lock:
            if self._context:
                self._native.acvision_runtime_destroy(self._context)
                self._context = None

    def __enter__(self):
        return self

    def __exit__(self, *exceptions):
        self.close()
