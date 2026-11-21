"""Rerun reference evaluation in a temporary directory and compare numerical files."""

import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from tabularshield.data import ROOT
from tabularshield.experiment import run

reference = json.loads((ROOT / "reports/run_manifest.json").read_text())
with tempfile.TemporaryDirectory(prefix="tabularshield-reproduction-") as temporary:
    path = Path(temporary)
    actual = run(path, seeds=reference["seeds"])
    verified = []
    for filename in [
        "experiment_results.csv",
        "summary.csv",
        "data_profiles.csv",
        "paired_comparisons.csv",
        "spatial_cells.csv",
        "averaging_attack.csv",
    ]:
        expected_frame = pd.read_csv(ROOT / "reports" / filename)
        actual_frame = pd.read_csv(path / filename)
        pd.testing.assert_frame_equal(expected_frame, actual_frame, rtol=1e-10, atol=1e-10)
        verified.append(filename)
    for filename in ["reconstruction.json", "spatial_diagnostics.json"]:
        assert json.loads((ROOT / "reports" / filename).read_text()) == json.loads(
            (path / filename).read_text()
        )
        verified.append(filename)
    assert actual["dataset_sha256"] == reference["dataset_sha256"]
    assert np.isfinite(pd.read_csv(path / "experiment_results.csv").coverage).all()
    record = {
        "status": "passed",
        "seeds": reference["seeds"],
        "files_verified": verified,
        "reference_sha256": reference["results_sha256"],
        "rerun_sha256": hashlib.sha256((path / "experiment_results.csv").read_bytes()).hexdigest(),
        "timing_excluded": True,
    }
(ROOT / "reports/reproduction-check.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
