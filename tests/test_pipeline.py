import json
from pathlib import Path

import numpy as np
import pandas as pd

from tabularshield.experiment import run
from tabularshield.report import build_report


def test_end_to_end_research_pipeline_and_report(tmp_path):
    record = run(tmp_path, seeds=2)
    assert record["experiment_rows"] == 540
    assert record["query_workloads"] == 27
    assert record["public_records"] > 5000
    results = pd.read_csv(tmp_path / "experiment_results.csv")
    assert results.groupby(["dataset", "measure", "dimensions", "seed"]).size().eq(10).all()
    raw = results[results.method == "raw"]
    assert raw.coverage.eq(1).all()
    assert raw.wape_visible.eq(0).all()
    assert raw[raw.unsafe_cells > 0].sensitive_near_truth_rate.eq(1).all()
    assert results.coverage.between(0, 1).all()
    reconstruction = json.loads((tmp_path / "reconstruction.json").read_text())
    assert reconstruction["exactly_reconstructable_before"] > 0
    assert reconstruction["exactly_reconstructable_after"] == 0
    primary = np.array(reconstruction["primary_mask"])
    truth = np.array(reconstruction["truth"])
    lower = np.array(reconstruction["final_intervals"]["lower"])
    upper = np.array(reconstruction["final_intervals"]["upper"])
    assert np.all(upper[primary] - lower[primary] >= 0.2 * truth[primary] - 1e-6)
    build_report(tmp_path)
    document = (tmp_path / "report.html").read_text()
    assert "data:image/png;base64," in document
    assert "<select" in document
    assert "<script src=" not in document
    assert "2 paired key seeds in this run" in (tmp_path / "RESEARCH_REPORT.md").read_text()
    assert len(list((tmp_path / "figures").glob("*.png"))) == 5
    decision = json.loads((tmp_path / "release_decision.json").read_text())
    assert decision["visible_cells_before"] == 16
    assert decision["visible_cells_after"] == 11
    assert decision["total_cells"] == 18
    assert np.isclose(decision["coverage_loss_percentage_points"], 100 * 5 / 18)
    assert decision["exactly_reconstructable_after"] == 0
    assert not decision["margins_withheld"]
    note = (tmp_path / "RELEASE_DECISION_NOTE.md").read_text()
    assert "88.9%" in note and "61.1%" in note
    assert "linked tables" in note


def test_committed_reference_has_complete_workload():
    root = Path(__file__).resolve().parents[1]
    if not (root / "reports/experiment_results.csv").exists():
        return  # Source package may intentionally exclude generated reports.
    results = pd.read_csv(root / "reports/experiment_results.csv")
    assert len(results) == 8100
    assert results.seed.nunique() == 30
    assert results.method.nunique() == 7
    assert results.delta.nunique() == 4
