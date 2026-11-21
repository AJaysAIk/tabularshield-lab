"""Point-neighbourhood diagnostics, using public WGS84 settlement centroids."""

import numpy as np
from scipy.spatial.distance import cdist


def weights(coordinates: np.ndarray, k: int = 4) -> np.ndarray:
    coordinates = np.asarray(coordinates, dtype=float)
    if coordinates.ndim != 2 or coordinates.shape[1] != 2 or not np.isfinite(coordinates).all():
        raise ValueError("Expected finite [latitude, longitude] pairs")
    n = len(coordinates)
    if not 1 <= k < n:
        raise ValueError("k must be smaller than number of points")
    lat, lon = np.radians(coordinates).T
    # Great-circle ordering, avoiding raw latitude/longitude Euclidean distances.
    sphere = np.c_[np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)]
    distances = cdist(sphere, sphere)
    np.fill_diagonal(distances, np.inf)
    neighbours = np.argsort(distances, axis=1, kind="stable")[:, :k]
    adjacency = np.zeros((n, n))
    adjacency[np.arange(n)[:, None], neighbours] = 1
    # Symmetric binary kNN graph; no implicit polygon-contiguity assumption.
    return np.maximum(adjacency, adjacency.T)


def moran_i(values: np.ndarray, adjacency: np.ndarray) -> float | None:
    values = np.asarray(values, dtype=float)
    adjacency = np.asarray(adjacency, dtype=float)
    if (
        adjacency.shape != (len(values), len(values))
        or not np.isfinite(values).all()
        or not np.isfinite(adjacency).all()
        or (adjacency < 0).any()
    ):
        raise ValueError("Invalid spatial inputs")
    centred = values - values.mean()
    denominator = centred @ centred
    if denominator <= 1e-24 or adjacency.sum() == 0:
        return None
    return float(len(values) / adjacency.sum() * (centred @ adjacency @ centred) / denominator)


def permutation_test(
    values: np.ndarray, adjacency: np.ndarray, permutations: int = 199, seed: int = 909
) -> dict:
    observed = moran_i(values, adjacency)
    if permutations < 1:
        raise ValueError("Positive permutation count required")
    if observed is None:
        return {"moran_i": None, "p_two_sided": None, "permutations": permutations}
    rng = np.random.default_rng(seed)
    expected = -1 / (len(values) - 1)
    exceed = sum(
        abs(moran_i(rng.permutation(values), adjacency) - expected) >= abs(observed - expected)
        for _ in range(permutations)
    )
    return {
        "moran_i": observed,
        "p_two_sided": (exceed + 1) / (permutations + 1),
        "permutations": permutations,
    }
