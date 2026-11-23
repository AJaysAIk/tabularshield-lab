"""Generate standalone findings and charts from recorded results, never hand-picked scores."""

import base64
import html
import json
import os
import re
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/tabularshield-mpl")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import ROOT

COLORS = {
    "raw": "#6b7280",
    "primary_suppression": "#d97706",
    "rounding": "#0891b2",
    "winsor_only": "#dc2626",
    "iid_noise": "#9333ea",
    "keyed_noise": "#2563eb",
    "winsor_keyed": "#059669",
}


def build_report(output: Path = ROOT / "reports") -> None:
    output = Path(output)
    figures = output / "figures"
    figures.mkdir(exist_ok=True)
    manifest = json.loads((output / "run_manifest.json").read_text())
    summary = pd.read_csv(output / "summary.csv")
    base = summary[np.isclose(summary.delta, 0.2)]
    reconstruction = json.loads((output / "reconstruction.json").read_text())
    averaging = pd.read_csv(output / "averaging_attack.csv")
    geo = pd.read_csv(output / "spatial_cells.csv")
    spatial = json.loads((output / "spatial_diagnostics.json").read_text())
    truth = np.asarray(reconstruction["truth"], dtype=float)
    primary_mask = np.asarray(reconstruction["primary_mask"], dtype=bool)
    final_mask = np.asarray(reconstruction["final_mask"], dtype=bool)
    if truth.shape != primary_mask.shape or truth.shape != final_mask.shape:
        raise ValueError("Reconstruction truth and suppression masks must have matching shapes")
    if np.any(primary_mask & ~final_mask):
        raise ValueError("Complementary suppression must retain every primary suppression")
    total_cells = int(truth.size)
    before_visible = int((~primary_mask).sum())
    after_visible = int((~final_mask).sum())
    added = int((final_mask & ~primary_mask).sum())
    if added != reconstruction["additional_suppressions"]:
        raise ValueError("Recorded additional suppressions disagree with the masks")
    decision = {
        "dataset": reconstruction["dataset"],
        "measure": reconstruction["measure"],
        "total_cells": total_cells,
        "primary_cells": int(primary_mask.sum()),
        "additional_suppressions": added,
        "visible_cells_before": before_visible,
        "visible_cells_after": after_visible,
        "coverage_before": before_visible / total_cells,
        "coverage_after": after_visible / total_cells,
        "coverage_loss_percentage_points": 100 * added / total_cells,
        "exactly_reconstructable_before": reconstruction["exactly_reconstructable_before"],
        "exactly_reconstructable_after": reconstruction["exactly_reconstructable_after"],
        "margins_withheld": reconstruction["margins_withheld"],
        "scope": "One recorded table; visible cells, exact margins and nonnegativity",
    }
    (output / "release_decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    decision_note = f"""# Release decision: what the extra suppression changes

## Decision being considered
Whether to publish the recorded Wholesale {reconstruction['measure']} table with primary suppression alone or with the tested additional suppressions. This is a worked public-data example for discussion with a statistical-data publisher.

## Evidence
The table has {total_cells} cells. Primary suppression hides {decision['primary_cells']}, leaving {before_visible}/{total_cells} ({100 * decision['coverage_before']:.1f}%) visible. Exact row and column totals let an attacker recover both initially hidden cells exactly. Adding {added} suppressions leaves {after_visible}/{total_cells} ({100 * decision['coverage_after']:.1f}%) visible: a loss of {decision['coverage_loss_percentage_points']:.1f} percentage points of cell coverage. Exact recovery of primary cells falls from {decision['exactly_reconstructable_before']} to {decision['exactly_reconstructable_after']} under the recorded attacker constraints. Row and column totals remain available.

## What a user gains and loses
The initially flagged values cannot be uniquely recovered in this model. The user loses five additional cell values, so some detailed comparisons are no longer possible. Published cells stay unchanged, but visible-cell error alone misses the cost of withheld cells; coverage must be reported with it. Totals still support broader comparisons.

## Recommendation for review
Treat complementary suppression as a candidate where retaining exact margins matters. Compare its loss of detailed cells with perturbation's numerical distortion, using the same user queries. No method is recommended solely because it blocks this one reconstruction.

## Before recommending it for a real release
- Agree which outputs users need and acceptable losses of detail with the data owner.
- Retest reconstruction with linked tables, repeated releases and plausible background knowledge.
- Compare suppression and perturbation on the same workloads, including coverage, error and uncertainty across paired runs.
- Test skewed distributions, small groups and spatial sensitivity; have a disclosure-control specialist review thresholds and assumptions.
- Record a release policy and obtain approval before any confidential-data deployment.

## Statistical foundations applied
Descriptive analysis profiles missingness, spread and skew across three public datasets. Paired comparisons and 95% intervals across key seeds measure variation in fixed-query experiments; they are not population confidence intervals. A permutation test examines geographic residual clustering. The release calculation above applies percentages and constrained optimisation to explain a privacy-utility decision in plain English.

## Source and reproducibility
Derived from `reconstruction.json`; the wider evidence is in `data_profiles.csv`, `paired_comparisons.csv` and `spatial_diagnostics.json`. Rebuild with `python -m tabularshield report`. This is a prepared decision note, not evidence of a completed client presentation or an approved release policy.
"""
    (output / "RELEASE_DECISION_NOTE.md").write_text(decision_note)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.dpi": 160,
            "figure.facecolor": "#ffffff",
        }
    )
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.4))
    markers = dict(zip(COLORS, ["x", "s", "o", "D", "v", "^", "P"], strict=True))
    for ax, (name, block) in zip(axes, base.groupby("dataset"), strict=True):
        pivot = block.pivot(index="method", columns="metric", values="mean")
        for method, row in pivot.iterrows():
            if pd.notna(row.wape_visible) and pd.notna(row.sensitive_near_truth_rate):
                ax.scatter(
                    row.wape_visible * 100,
                    row.sensitive_near_truth_rate * 100,
                    s=75,
                    color=COLORS[method],
                    label=method,
                    marker=markers[method],
                )
        ax.set(
            title=name,
            xlabel="Visible-cell WAPE (%)",
            ylabel="Sensitive cells within 5% of truth (%)",
        )
        ax.grid(alpha=0.2)
    fig.suptitle(
        "Risk proxy versus utility — interpret together with release coverage", fontsize=14
    )
    from matplotlib.lines import Line2D

    handles = [
        Line2D([], [], color=COLORS[name], marker=markers[name], linestyle="", label=name)
        for name in COLORS
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0.12, 1, 0.94))
    fig.savefig(figures / "risk_utility.png", bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    stages = ["Primary only", "+ complementary"]
    counts = [
        [decision["exactly_reconstructable_before"], decision["exactly_reconstructable_after"]],
        [before_visible, after_visible],
    ]
    for ax, values, title, denominator in zip(
        axes,
        counts,
        ["Flagged cells recoverable exactly", "Cell values still published"],
        [decision["primary_cells"], total_cells],
        strict=True,
    ):
        bars = ax.bar(stages, values, color=["#d97706", "#2563eb"])
        ax.bar_label(bars, labels=[f"{v}/{denominator}" for v in values], padding=5)
        ax.set(title=title, ylabel="Number of cells", ylim=(0, denominator * 1.2))
        ax.set_yticks(range(0, denominator + 1, max(1, denominator // 6)))
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("A release decision: less reconstruction, fewer detailed values")
    fig.tight_layout()
    fig.savefig(figures / "release_decision.png", bbox_inches="tight")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for name, block in summary[summary.method == "keyed_noise"].groupby("dataset"):
        for ax, metric in zip(axes, ["wape_visible", "sensitive_near_truth_rate"], strict=True):
            rows = block[block.metric == metric].sort_values("delta")
            valid = rows[rows["mean"].notna()]
            ax.errorbar(
                valid.delta,
                valid["mean"] * 100,
                yerr=(valid.ci_high - valid.ci_low) * 50,
                marker="o",
                capsize=3,
                label=name,
            )
            ax.set(xlabel="Noise scale delta", ylabel=metric + " (%)")
            ax.grid(alpha=0.2)
    axes[0].legend()
    fig.suptitle(f"Scale ablation — 95% intervals across {manifest['seeds']} paired key seeds")
    fig.tight_layout()
    fig.savefig(figures / "ablation.png", bbox_inches="tight")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.loglog(averaging.repeats, averaging.iid_rmse, "o-", label="Fresh IID noise per query")
    ax.loglog(averaging.repeats, averaging.fixed_key_rmse, "s-", label="Fixed-key noise")
    ax.set(
        xlabel="Identical query repetitions",
        ylabel="RMSE of averaged noise (source units)",
        title="Negative control: averaging defeats fresh noise",
    )
    ax.legend()
    ax.grid(alpha=0.2, which="both")
    fig.tight_layout()
    fig.savefig(figures / "averaging_attack.png", bbox_inches="tight")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.5, 7.0))
    scatter = ax.scatter(
        geo.longitude,
        geo.latitude,
        c=geo.relative_error * 100,
        cmap="RdBu_r",
        vmin=-20,
        vmax=20,
        s=25,
        edgecolor="white",
        linewidth=0.3,
    )
    fig.colorbar(scatter, ax=ax, label="Relative error in released population sums (%)")
    ax.set(
        xlabel="Longitude",
        ylabel="Latitude",
        title="Geographic residuals: public GB settlement aggregates",
    )
    ax.set_aspect(1.7)
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(figures / "spatial_errors.png", bbox_inches="tight")
    plt.close(fig)

    rows = []
    for (name, method), block in base.groupby(["dataset", "method"]):
        values = block.set_index("metric")["mean"]
        rows.append(
            {
                "dataset": name,
                "method": method,
                "coverage": values.coverage,
                "wape": values.wape_visible,
                "risk_proxy": values.sensitive_near_truth_rate,
            }
        )
    table = pd.DataFrame(rows)
    lines = [
        "| Dataset | Method | Coverage | Visible WAPE | Near-truth sensitive cells |",
        "|---|---|---:|---:|---:|",
    ]

    def pct(x):
        return "N/A" if pd.isna(x) else f"{100 * x:.2f}%"

    for row in rows:
        lines.append(
            f"| {row['dataset']} | {row['method']} | {pct(row['coverage'])} | {pct(row['wape'])} | {pct(row['risk_proxy'])} |"
        )
    attack_ratio = averaging.iloc[0].iid_rmse / averaging.iloc[-1].iid_rmse
    narrative = f"""# TabularShield Lab — research report

## Question and scope
Can magnitude-table protection methods preserve useful totals while reducing selected disclosure indicators? This research prototype compares methods using public data.

## Recorded experiment
- {len(json.loads((ROOT / "data/manifest.json").read_text()))} public datasets; {len(pd.read_csv(output / "data_profiles.csv"))} measure profiles.
- {len(pd.read_csv(output / "experiment_results.csv")):,} method/workload/seed evaluations, including scale ablations.
- {manifest["seeds"]} paired key seeds in this run. Query families and parameters fixed in [protocol](../docs/protocol.json).
- Numerical output SHA-256: `{manifest["results_sha256"]}`.

## Results at delta = 0.20
Queries are macro-averaged within each dataset. WAPE is calculated on visible cells only. Coverage is separate so withholding is never rewarded as perfect accuracy. The risk proxy is the fraction of originally flagged cells whose published values remain within 5% of truth. It is **not** an estimated probability of re-identification. Empty risk denominators are N/A.

{chr(10).join(lines)}

## Adversarial checks
**Exact margins:** In the recorded {reconstruction["shape"][0]}×{reconstruction["shape"][1]} wholesale table, {reconstruction["primary_cells"]} cells were initially flagged. An attacker using visible cells, nonnegativity and exact margins could reconstruct {reconstruction["exactly_reconstructable_before"]} primary cells exactly. Greedy complementary suppression added {reconstruction["additional_suppressions"]} suppressions; exactly recoverable primary cells afterward: {reconstruction["exactly_reconstructable_after"]}. Margin withholding: {reconstruction["margins_withheld"]}. This check is scoped to one two-dimensional table and the stated constraints, not arbitrary linked queries or background information.

**Repeated identical queries:** Across 200 random noise realizations, increasing repetitions from 1 to 1,000 reduced fresh-noise averaging RMSE by {attack_ratio:.1f}×. Fixed-key RMSE stayed constant. Both use the same lookup-noise distribution and scale. Fixed keys address this averaging attack only; they do not establish general confidentiality.

## What a release user gains and loses
Additional suppression prevents exact recovery of the {decision['primary_cells']} flagged cells under the tested constraints. It reduces available cell values from {before_visible}/{total_cells} ({100 * decision['coverage_before']:.1f}%) to {after_visible}/{total_cells} ({100 * decision['coverage_after']:.1f}%). Users lose {added} detailed values, or {decision['coverage_loss_percentage_points']:.1f} percentage points of coverage, while row and column totals remain available. Compare this cost with the distortion introduced by perturbation before choosing a release method. The repository includes a release decision note with review questions and the underlying calculation.

## Geographic strand
{spatial["cells"]} occupied half-degree grid cells from real GeoNames GB settlement coordinates. The primary symmetric 4-neighbour graph yields residual Moran's I = {spatial["moran_i"]:.4f}, permutation p = {spatial["p_two_sided"]:.3f} (199 permutations). Neighbour sensitivity k = 2/4/8 is recorded separately. These are exploratory diagnostics, without a multiple-testing claim. Point neighbours are not administrative polygon contiguity. Settlement populations can overlap and have mixed reference years; their sum is not a UK population estimate.

## Interpretation and decisions
1. Suppression must be assessed with its publication coverage and margin constraints. A low direct risk proxy can coexist with exact reconstruction.
2. A public fixed key is suitable for reproducibility, not confidential deployment. A production key and release lifecycle need separate security design.
3. Capping trades reduced dominance for downward distortion. Compare the paired capping ablation rather than assuming it is beneficial.
4. Increasing perturbation changes the utility/risk proxy trade-off. No setting is called universally optimal or privacy-safe.
5. Integration evidence is a bounded read-only API demonstration. Actual Cantabular integration, calibrated disclosure policy and independent domain review remain future work.

## Uncertainty
The 95% t intervals describe variability across key seeds on fixed datasets and fixed queries. They are not population confidence intervals. Deterministic methods have zero seed variability. Queries share records and are not independent replicates. See [paired contrasts](paired_comparisons.csv), [raw evaluations](experiment_results.csv), [limitations](../docs/limitations.md) and [data profiles](data_profiles.csv).

## Reproduce and review
Run the README commands, then `python scripts/verify_reproduction.py`. All source-data transformations, digests, tests and failure assumptions are available for inspection. No claims about user mastery, client delivery, agency experience or peer review are inferred from these results.
"""
    (output / "RESEARCH_REPORT.md").write_text(narrative)
    image_blocks = []
    for name in ["release_decision", "risk_utility", "ablation", "averaging_attack", "spatial_errors"]:
        encoded = base64.b64encode((figures / f"{name}.png").read_bytes()).decode()
        image_blocks.append(
            f'<figure><img alt="{name.replace("_", " ")}" src="data:image/png;base64,{encoded}"></figure>'
        )
    data_table = table.to_html(index=False, classes="results", float_format=lambda x: f"{x:.5f}")

    # Locally generated trusted text; escape before embedding, never execute report input.
    def inline(text):
        safe = html.escape(text)
        safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
        return re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)

    paragraphs = []
    for paragraph in narrative.split("\n\n"):
        if paragraph.startswith("|"):
            continue
        if paragraph.startswith("## "):
            paragraphs.append(f"<h3>{inline(paragraph[3:])}</h3>")
        elif paragraph.startswith("# "):
            paragraphs.append(f"<h2>{inline(paragraph[2:])}</h2>")
        elif paragraph.startswith("- "):
            paragraphs.append(
                "<ul>"
                + "".join(f"<li>{inline(line[2:])}</li>" for line in paragraph.splitlines())
                + "</ul>"
            )
        else:
            paragraphs.append(f"<p>{inline(paragraph)}</p>")
    rendered = "\n".join(paragraphs)
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TabularShield — evidence and trade-offs</title><style>
body{{font:16px/1.65 system-ui,sans-serif;background:#f4f6fa;color:#172033;margin:0}}main{{max-width:1120px;margin:auto;padding:42px 24px}}h1{{font-size:44px;line-height:1.1}}.tag{{color:#5460b4;font-weight:700;letter-spacing:.1em;font-size:12px}}.card,figure{{background:white;border:1px solid #dce2ed;border-radius:16px;padding:24px;margin:24px 0}}img{{max-width:100%;height:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border-bottom:1px solid #e2e7f0;padding:9px;text-align:left}}select{{padding:10px;font:inherit;border-radius:8px}}.scroll{{overflow:auto}}p{{white-space:pre-wrap;overflow-wrap:anywhere}}footer{{color:#5b677e;font-size:13px}}a{{color:#2549b4}}</style></head><body><main>
<div class="tag">PUBLIC DATA · REPRODUCIBLE RESEARCH · SOFTWARE EVIDENCE</div><h1>Useful statistics.<br>Measurable trade-offs.</h1><p>TabularShield Lab — magnitude-table protection, attack evaluation and geographic diagnostics.</p>
<div class="card"><strong>Research prototype.</strong></div>
{"".join(image_blocks)}<section class="card"><h2>Explore the recorded comparison</h2><label for="dataset">Dataset </label><select id="dataset"><option value="all">All datasets</option><option>wholesale</option><option>abalone</option><option>geonames_gb</option></select><p>Rates are fractions (0–1). WAPE is measured only on published cells; compare coverage alongside it.</p><div class="scroll">{data_table}</div></section><section class="card"><h2>Full findings and assumptions</h2>{rendered}</section><footer>Ajay Sai Kummara · Licence and source attribution are in the repository. This report contains no external scripts, trackers or remote resources.</footer></main><script>document.getElementById('dataset').addEventListener('change',function(){{document.querySelectorAll('table.results tbody tr').forEach(row=>{{row.hidden=this.value!=='all'&&row.cells[0].textContent.trim()!==this.value}})}});</script></body></html>"""
    (output / "report.html").write_text(document)
    print(f"Report written to {output / 'report.html'}")
