"""Magnitude-table experiments. All risk measures here are empirical proxies.

Record keys are fixed within a dataset/measure/seed; member-equivalent queries
receive equal perturbations. Public experiment seeds are NOT operational secrets.
"""

import hashlib
import hmac
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

METHODS = (
    "raw",
    "primary_suppression",
    "rounding",
    "winsor_only",
    "iid_noise",
    "keyed_noise",
    "winsor_keyed",
)
MODULUS = 4096


@dataclass(frozen=True)
class Policy:
    min_count: int = 5
    dominance_threshold: float = 0.85
    delta: float = 0.20
    cap_quantile: float = 0.95

    def __post_init__(self):
        if type(self.min_count) is not int or self.min_count < 1:
            raise ValueError("min_count must be a positive integer")
        if not 0 < self.dominance_threshold <= 1:
            raise ValueError("Invalid dominance threshold")
        if not math.isfinite(self.delta) or not 0 < self.delta <= 0.5:
            raise ValueError("delta must be in (0, 0.5]")
        if not 0 < self.cap_quantile <= 1:
            raise ValueError("Invalid cap quantile")


def record_keys(ids, secret: bytes, namespace: str) -> np.ndarray:
    if not secret:
        raise ValueError("A nonempty key is required")
    return np.array(
        [
            int.from_bytes(
                hmac.new(secret, f"{namespace}\0{x}".encode(), hashlib.sha256).digest()[:8], "big"
            )
            % MODULUS
            for x in ids
        ],
        dtype=np.int64,
    )


def ptable(keys) -> np.ndarray:
    """Illustrative symmetric distribution, not an official calibrated p-table."""
    u = (np.asarray(keys, dtype=np.int64) % MODULUS + 0.5) / MODULUS
    return np.select(
        [u < 0.125, u < 0.375, u < 0.625, u < 0.875], [-1.0, -0.5, 0.0, 0.5], default=1.0
    )


def aggregate(
    frame: pd.DataFrame,
    dimensions: tuple[str, ...],
    measure: str,
    secret: bytes,
    namespace: str,
    policy: Policy = Policy(),
) -> pd.DataFrame:
    if not dimensions or len(set(dimensions)) != len(dimensions):
        raise ValueError("Supply unique grouping dimensions")
    if measure in dimensions or not set(["unit_id", measure, *dimensions]).issubset(frame):
        raise ValueError("Invalid measure/grouping columns")
    if frame.empty or frame[["unit_id", measure, *dimensions]].isna().any().any():
        raise ValueError("Missing values or empty input")
    if frame.unit_id.duplicated().any():
        raise ValueError("Duplicate contributor IDs")
    values = frame[measure].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Finite nonnegative measures required")
    work = frame[["unit_id", *dimensions]].copy()
    work["_value"] = values
    work["_capped"] = np.minimum(values, np.quantile(values, policy.cap_quantile))
    work["_key"] = record_keys(work.unit_id, secret, namespace)
    rows = []
    # Sort values before summing: stable results even when input row order changes.
    for group, part in work.groupby(list(dimensions), sort=True, observed=True):
        group = group if isinstance(group, tuple) else (group,)
        ordered = np.sort(part._value.to_numpy())
        capped = np.sort(part._capped.to_numpy())
        total = math.fsum(ordered)
        top2 = math.fsum(ordered[-2:]) / total if total else 0.0
        rows.append(
            {
                **dict(zip(dimensions, group, strict=True)),
                "count": len(part),
                "truth": total,
                "max_value": float(ordered[-1]),
                "top2_share": top2,
                "unsafe": len(part) < policy.min_count or top2 > policy.dominance_threshold,
                "capped_total": math.fsum(capped),
                "capped_max": float(capped[-1]),
                "cell_key": int(part._key.sum()) % MODULUS,
            }
        )
    return pd.DataFrame(rows)


def release(
    table: pd.DataFrame,
    method: str,
    policy: Policy = Policy(),
    rng: np.random.Generator | None = None,
    rounding_base: float = 1.0,
) -> np.ndarray:
    truth = table.truth.to_numpy(dtype=float)
    if method == "raw":
        return truth.copy()
    if method == "primary_suppression":
        return np.where(table.unsafe, np.nan, truth)
    if method == "rounding":
        if not math.isfinite(rounding_base) or rounding_base <= 0:
            raise ValueError("Invalid rounding base")
        return np.floor(truth / rounding_base + 0.5) * rounding_base
    if method == "winsor_only":
        return table.capped_total.to_numpy(dtype=float).copy()
    if method not in {"iid_noise", "keyed_noise", "winsor_keyed"}:
        raise ValueError("Unknown method")
    if method == "iid_noise":
        if rng is None:
            raise ValueError("IID experiments require an explicit RNG")
        noise = ptable(rng.integers(0, MODULUS, size=len(table)))
    else:
        noise = ptable(table.cell_key.to_numpy())
    cap = method == "winsor_keyed"
    base = table.capped_total.to_numpy() if cap else truth
    scale = table.capped_max.to_numpy() if cap else table.max_value.to_numpy()
    # Nonnegative by construction: max <= total and delta <= .5, |noise| <= 1.
    return base + policy.delta * scale * noise


def metrics(table: pd.DataFrame, released: np.ndarray) -> dict:
    truth = table.truth.to_numpy(dtype=float)
    released = np.asarray(released, dtype=float)
    if released.shape != truth.shape or np.isinf(released).any():
        raise ValueError("Invalid release shape or infinity")
    visible = np.isfinite(released)
    errors = np.abs(released[visible] - truth[visible])
    denominator = truth[visible].sum()
    unsafe = table.unsafe.to_numpy(dtype=bool)
    close = visible & (np.abs(released - truth) <= 0.05 * truth)
    return {
        "cells": len(table),
        "unsafe_cells": int(unsafe.sum()),
        "coverage": float(visible.mean()),
        "wape_visible": float(errors.sum() / denominator) if denominator else None,
        "mae_visible": float(errors.mean()) if len(errors) else None,
        "retained_truth_share": float(truth[visible].sum() / truth.sum()) if truth.sum() else None,
        "sensitive_near_truth_rate": float(close[unsafe].mean()) if unsafe.any() else None,
        "unchanged_visible_rate": float(
            np.isclose(released[visible], truth[visible], rtol=0, atol=1e-10).mean()
        )
        if visible.any()
        else None,
    }
