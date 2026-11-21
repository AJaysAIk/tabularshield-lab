"""Fixed query workload, paired key seeds, seed-level intervals and negative controls."""

import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

from .attacks import averaging_attack, complementary_suppression, linear_intervals
from .core import Policy, aggregate, metrics, release
from .data import ROOT, load_dataset
from .spatial import permutation_test, weights

METHODS = (
    "raw",
    "primary_suppression",
    "rounding",
    "winsor_only",
    "iid_noise",
    "keyed_noise",
    "winsor_keyed",
)


def summarise(results: pd.DataFrame) -> pd.DataFrame:
    output = []
    metric_columns = [
        "coverage",
        "wape_visible",
        "sensitive_near_truth_rate",
        "unchanged_visible_rate",
        "retained_truth_share",
    ]
    # Query workload is fixed. CIs quantify key randomization only, not population uncertainty.
    for (dataset, method, delta), block in results.groupby(["dataset", "method", "delta"]):
        for metric in metric_columns:
            seeds = block.groupby("seed")[metric].mean().dropna()
            mean = float(seeds.mean()) if len(seeds) else None
            half = float(t.ppf(0.975, len(seeds) - 1) * seeds.sem()) if len(seeds) > 1 else 0.0
            output.append(
                {
                    "dataset": dataset,
                    "method": method,
                    "delta": delta,
                    "metric": metric,
                    "mean": mean,
                    "ci_low": mean - half if mean is not None else None,
                    "ci_high": mean + half if mean is not None else None,
                    "seed_count": len(seeds),
                    "scope": "fixed-workload key-randomization uncertainty",
                }
            )
    return pd.DataFrame(output)


def attack_study(source) -> dict:
    f = source.frame.copy()
    f["column_group"] = f.Channel.astype(str) + ":" + f.spend_band.astype(str)
    table = aggregate(f, ("Region", "column_group"), "Delicassen", b"attack-study", source.digest)
    matrix = (
        table.pivot(index="Region", columns="column_group", values="truth").fillna(0).to_numpy()
    )
    mask = (
        table.pivot(index="Region", columns="column_group", values="unsafe")
        .fillna(False)
        .astype(bool)
        .to_numpy()
    )
    before = np.where(mask, np.nan, matrix)
    lo, hi = linear_intervals(before, matrix.sum(axis=1), matrix.sum(axis=0))
    after = complementary_suppression(matrix, mask)
    exact_before = int(((hi - lo < 1e-6) & mask).sum())
    if after["margins_withheld"]:
        exact_after = None
    else:
        exact_after = int(((after["upper"] - after["lower"] < 1e-6) & mask).sum())
    return {
        "dataset": source.name,
        "measure": "Delicassen",
        "shape": list(matrix.shape),
        "threat": "attacker knows unsuppressed cells, exact row/column margins and nonnegativity",
        "primary_cells": int(mask.sum()),
        "exactly_reconstructable_before": exact_before,
        "exactly_reconstructable_after": exact_after,
        "additional_suppressions": int(after["mask"].sum() - mask.sum()),
        "margins_withheld": after["margins_withheld"],
        "target_interval_width_fraction": 0.20,
        "truth": matrix.tolist(),
        "primary_mask": mask.tolist(),
        "primary_intervals": {"lower": lo.tolist(), "upper": hi.tolist()},
        "final_mask": after["mask"].tolist(),
        "final_intervals": None
        if after["margins_withheld"]
        else {"lower": after["lower"].tolist(), "upper": after["upper"].tolist()},
    }


def spatial_study(source) -> tuple[pd.DataFrame, dict]:
    dimensions = ("lat_band", "lon_band")
    table = aggregate(source.frame, dimensions, "population", b"spatial-study", source.digest)
    centers = (
        source.frame.groupby(list(dimensions), sort=True)[["latitude", "longitude"]]
        .mean()
        .reset_index()
    )
    table = table.merge(centers, on=list(dimensions), validate="one_to_one")
    table["released"] = release(table, "keyed_noise")
    table["relative_error"] = (table.released - table.truth) / table.truth
    graph = weights(table[["latitude", "longitude"]].to_numpy(), 4)
    sensitivity = []
    for k in [2, 4, 8]:
        adjacency = weights(table[["latitude", "longitude"]].to_numpy(), k)
        sensitivity.append({"k": k, **permutation_test(table.relative_error.to_numpy(), adjacency)})
    diagnostics = {
        "cells": len(table),
        "unit": "reported settlement population aggregates; not household disclosure risk",
        "graph": "symmetric binary nearest-neighbour graph on great-circle ordering",
        "primary_k": 4,
        **permutation_test(table.relative_error.to_numpy(), graph),
        "sensitivity": sensitivity,
        "interpretation": "Exploratory residual-pattern diagnostic; no spatial privacy guarantee or population inference.",
    }
    return table, diagnostics


def run(output: Path = ROOT / "reports", seeds: int = 30) -> dict:
    if seeds < 2:
        raise ValueError("At least two paired seeds required")
    output.mkdir(parents=True, exist_ok=True)
    sources = [load_dataset(name) for name in ["wholesale", "abalone", "geonames_gb"]]
    rows, profiles, runtime = [], [], []
    start = time.perf_counter()
    for source in sources:
        print(f"Evaluating {source.name}: {len(source.frame):,} public records", flush=True)
        for measure in source.measures:
            values = source.frame[measure]
            profiles.append(
                {
                    "dataset": source.name,
                    "measure": measure,
                    "n": len(values),
                    "mean": values.mean(),
                    "median": values.median(),
                    "std": values.std(),
                    "q25": values.quantile(0.25),
                    "q75": values.quantile(0.75),
                    "p95": values.quantile(0.95),
                    "max": values.max(),
                    "zero_count": int((values == 0).sum()),
                    "missing": int(values.isna().sum()),
                }
            )
            for dimensions in source.workloads:
                base = max(float(values.median()) * 0.1, 1e-6)
                for seed in range(seeds):
                    secret = f"PUBLIC-research-key-{seed}".encode()
                    tick = time.perf_counter()
                    table = aggregate(
                        source.frame, dimensions, measure, secret, source.digest + ":" + measure
                    )
                    if seed < 5:
                        runtime.append(
                            {
                                "dataset": source.name,
                                "rows": len(source.frame),
                                "cells": len(table),
                                "milliseconds": (time.perf_counter() - tick) * 1000,
                            }
                        )
                    for method in METHODS:
                        released = release(
                            table,
                            method,
                            rng=np.random.default_rng(seed + 10000),
                            rounding_base=base,
                        )
                        rows.append(
                            {
                                "dataset": source.name,
                                "measure": measure,
                                "dimensions": "+".join(dimensions),
                                "seed": seed,
                                "method": method,
                                "delta": 0.20,
                                **metrics(table, released),
                            }
                        )
                    for delta in [0.05, 0.10, 0.40]:
                        released = release(table, "keyed_noise", Policy(delta=delta))
                        rows.append(
                            {
                                "dataset": source.name,
                                "measure": measure,
                                "dimensions": "+".join(dimensions),
                                "seed": seed,
                                "method": "keyed_noise",
                                "delta": delta,
                                **metrics(table, released),
                            }
                        )
    results = pd.DataFrame(rows)
    results.to_csv(output / "experiment_results.csv", index=False, float_format="%.12g")
    summarise(results).to_csv(output / "summary.csv", index=False, float_format="%.12g")
    pd.DataFrame(profiles).to_csv(output / "data_profiles.csv", index=False)
    attacks = attack_study(sources[0])
    (output / "reconstruction.json").write_text(json.dumps(attacks, indent=2) + "\n")
    table, diagnostics = spatial_study(sources[2])
    table.to_csv(output / "spatial_cells.csv", index=False)
    (output / "spatial_diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    target = aggregate(
        sources[0].frame, ("Region", "Channel"), "Fresh", b"averaging", sources[0].digest
    )
    scale = 0.2 * target.max_value.max()
    averaging = averaging_attack(scale)
    pd.DataFrame(averaging).to_csv(output / "averaging_attack.csv", index=False)
    paired = []
    selected = results[
        (results.delta == 0.20) & results.method.isin(["keyed_noise", "winsor_keyed"])
    ]
    for name, block in selected.groupby("dataset"):
        for metric in ["wape_visible", "sensitive_near_truth_rate"]:
            pivot = block.groupby(["seed", "method"])[metric].mean().unstack()
            difference = (pivot.winsor_keyed - pivot.keyed_noise).dropna()
            half = (
                t.ppf(0.975, len(difference) - 1) * difference.sem() if len(difference) > 1 else 0.0
            )
            paired.append(
                {
                    "dataset": name,
                    "metric": metric,
                    "contrast": "winsor_keyed minus keyed_noise",
                    "mean_difference": difference.mean(),
                    "ci_low": difference.mean() - half,
                    "ci_high": difference.mean() + half,
                    "paired_seeds": len(difference),
                }
            )
    pd.DataFrame(paired).to_csv(output / "paired_comparisons.csv", index=False)
    metadata = {
        "seeds": seeds,
        "query_workloads": sum(len(x.measures) * len(x.workloads) for x in sources),
        "methods": list(METHODS),
        "delta_grid": [0.05, 0.10, 0.20, 0.40],
        "experiment_rows": len(rows),
        "public_records": sum(len(x.frame) for x in sources),
        "dataset_sha256": {x.name: x.digest for x in sources},
        "results_sha256": hashlib.sha256(
            (output / "experiment_results.csv").read_bytes()
        ).hexdigest(),
        "python": platform.python_version(),
        "uncertainty": "95% t intervals across key seeds; fixed datasets and queries",
        "scope": "Independent AI-assisted research prototype; no privacy certification, client work, or affiliation.",
    }
    (output / "run_manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (output / "benchmark.json").write_text(
        json.dumps(
            {"elapsed_seconds": time.perf_counter() - start, "measurements": runtime}, indent=2
        )
        + "\n"
    )
    return metadata
