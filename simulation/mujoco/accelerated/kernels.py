"""Small CUDA probe, separate from the actual MuJoCo physics implementation."""
import warp as wp


@wp.kernel
def square(values: wp.array(dtype=wp.float32), result: wp.array(dtype=wp.float32)):
    index = wp.tid()
    result[index] = values[index]*values[index]
