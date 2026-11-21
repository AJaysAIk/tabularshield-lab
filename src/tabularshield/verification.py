"""Numerical comparison with strict structure and discrete results."""

import math


def compare_nested(expected, actual, path="root", rtol=1e-10, atol=1e-10):
    """Allow solver/BLAS last-bit differences, never altered counts or schema."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) != set(actual):
            raise AssertionError(f"{path}: dictionary keys changed")
        for key in expected:
            compare_nested(expected[key], actual[key], f"{path}.{key}", rtol, atol)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise AssertionError(f"{path}: list shape changed")
        for i, (left, right) in enumerate(zip(expected, actual, strict=True)):
            compare_nested(left, right, f"{path}[{i}]", rtol, atol)
    elif isinstance(expected, float):
        if (
            type(actual) not in (int, float)
            or not math.isfinite(expected)
            or not math.isfinite(actual)
        ):
            raise AssertionError(f"{path}: nonfinite or nonnumeric result")
        if not math.isclose(expected, actual, rel_tol=rtol, abs_tol=atol):
            raise AssertionError(
                f"{path}: {expected!r} != {actual!r} within rtol={rtol}, atol={atol}"
            )
    elif type(expected) is not type(actual) or expected != actual:
        raise AssertionError(f"{path}: discrete value changed: {expected!r} != {actual!r}")
