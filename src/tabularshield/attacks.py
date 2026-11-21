"""Attacker-visible linear constraints; ground truth is not an attacker bound."""

import numpy as np
from scipy.optimize import linprog


def linear_intervals(
    published: np.ndarray, row_totals: np.ndarray, column_totals: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    published = np.asarray(published, dtype=float)
    rows, cols = published.shape
    row_totals = np.asarray(row_totals, dtype=float)
    column_totals = np.asarray(column_totals, dtype=float)
    if row_totals.shape != (rows,) or column_totals.shape != (cols,):
        raise ValueError("Margin dimensions do not match")
    if not np.isfinite(row_totals).all() or not np.isfinite(column_totals).all():
        raise ValueError("Finite exact margins required")
    if (
        (row_totals < 0).any()
        or (column_totals < 0).any()
        or np.isinf(published).any()
        or (published[np.isfinite(published)] < 0).any()
    ):
        raise ValueError("Nonnegative, finite released values required")
    constraints = np.zeros((rows + cols, rows * cols))
    for r in range(rows):
        constraints[r, r * cols : (r + 1) * cols] = 1
    for c in range(cols):
        constraints[rows + c, c::cols] = 1
    bounds = [(float(x), float(x)) if np.isfinite(x) else (0.0, None) for x in published.ravel()]
    rhs = np.r_[row_totals, column_totals]
    feasible = linprog(
        np.zeros(rows * cols), A_eq=constraints, b_eq=rhs, bounds=bounds, method="highs"
    )
    if not feasible.success:
        raise ValueError("Inconsistent or infeasible release constraints")
    lower, upper = [], []
    for i in range(rows * cols):
        if np.isfinite(published.ravel()[i]):
            lower.append(published.ravel()[i])
            upper.append(published.ravel()[i])
            continue
        objective = np.zeros(rows * cols)
        objective[i] = 1
        lo = linprog(objective, A_eq=constraints, b_eq=rhs, bounds=bounds, method="highs")
        hi = linprog(-objective, A_eq=constraints, b_eq=rhs, bounds=bounds, method="highs")
        if not lo.success or not hi.success:
            raise ValueError("Inconsistent or infeasible release constraints")
        lower.append(lo.fun)
        upper.append(-hi.fun)
    return np.array(lower).reshape(rows, cols), np.array(upper).reshape(rows, cols)


def complementary_suppression(
    truth: np.ndarray, primary: np.ndarray, relative_width: float = 0.20
) -> dict:
    """Greedy 2D demonstration, not optimal suppression or a general release policy.

    Add cheapest visible cell until each primary interval is wide enough. If even
    complete cell suppression is inadequate, withhold exact margins as well.
    """
    truth = np.asarray(truth, dtype=float)
    primary = np.asarray(primary, dtype=bool)
    if (
        truth.ndim != 2
        or truth.shape != primary.shape
        or not np.isfinite(truth).all()
        or (truth < 0).any()
    ):
        raise ValueError("Invalid nonnegative matrix or mask")
    if not 0 < relative_width <= 1:
        raise ValueError("Invalid interval width target")
    mask = primary.copy()
    target = relative_width * truth
    for _ in range(truth.size + 1):
        published = np.where(mask, np.nan, truth)
        lo, hi = linear_intervals(published, truth.sum(axis=1), truth.sum(axis=0))
        if np.all((hi - lo)[primary] + 1e-7 >= target[primary]):
            return {
                "published": published,
                "mask": mask,
                "lower": lo,
                "upper": hi,
                "margins_withheld": False,
            }
        choices = np.where(mask, np.inf, truth)
        if not np.isfinite(choices).any():
            return {
                "published": published,
                "mask": mask,
                "lower": None,
                "upper": None,
                "margins_withheld": True,
            }
        mask.flat[int(np.argmin(choices))] = True
    raise RuntimeError("Suppression iteration bound exceeded")


def averaging_attack(scale: float, repeats=(1, 10, 100, 1000), trials: int = 200) -> list[dict]:
    from .core import MODULUS, ptable

    if not np.isfinite(scale) or scale <= 0 or trials < 2:
        raise ValueError("Positive scale and at least two trials required")
    rng = np.random.default_rng(1776)
    stable_noise = ptable(rng.integers(0, MODULUS, size=trials))
    output = []
    for count in repeats:
        if count < 1:
            raise ValueError("Positive repeat counts required")
        independent = ptable(rng.integers(0, MODULUS, size=(trials, count))).mean(axis=1)
        output.append(
            {
                "repeats": count,
                "trials": trials,
                "iid_rmse": float(scale * np.sqrt(np.mean(independent**2))),
                "fixed_key_rmse": float(scale * np.sqrt(np.mean(stable_noise**2))),
            }
        )
    return output
