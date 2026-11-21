# TabularShield Lab — research report

## Question and scope
Can independently implemented magnitude-table protection methods preserve useful totals while reducing selected disclosure indicators? This is an AI-assisted public-data prototype, not a certified release system or a production integration.

## Recorded experiment
- 3 public datasets; 9 measure profiles.
- 8,100 method/workload/seed evaluations, including scale ablations.
- 30 paired key seeds in this run. Query families and parameters fixed in [protocol](../docs/protocol.json).
- Numerical output SHA-256: `3122940b062fd8248f44172e611694b15dda7b6689e3010623a9adeed1b38191`.

## Results at delta = 0.20
Queries are macro-averaged within each dataset. WAPE is calculated on visible cells only. Coverage is separate so withholding is never rewarded as perfect accuracy. The risk proxy is the fraction of originally flagged cells whose published values remain within 5% of truth. It is **not** an estimated probability of re-identification. Empty risk denominators are N/A.

| Dataset | Method | Coverage | Visible WAPE | Near-truth sensitive cells |
|---|---|---:|---:|---:|
| abalone | iid_noise | 100.00% | 0.07% | 70.00% |
| abalone | keyed_noise | 100.00% | 0.07% | 68.33% |
| abalone | primary_suppression | 95.96% | 0.00% | 0.00% |
| abalone | raw | 100.00% | 0.00% | 100.00% |
| abalone | rounding | 100.00% | 0.01% | 87.50% |
| abalone | winsor_keyed | 100.00% | 1.73% | 68.33% |
| abalone | winsor_only | 100.00% | 1.70% | 100.00% |
| geonames_gb | iid_noise | 100.00% | 3.44% | 33.02% |
| geonames_gb | keyed_noise | 100.00% | 3.44% | 33.77% |
| geonames_gb | primary_suppression | 63.23% | 0.00% | 0.00% |
| geonames_gb | raw | 100.00% | 0.00% | 100.00% |
| geonames_gb | rounding | 100.00% | 0.10% | 91.87% |
| geonames_gb | winsor_keyed | 100.00% | 27.45% | 32.56% |
| geonames_gb | winsor_only | 100.00% | 26.78% | 91.07% |
| wholesale | iid_noise | 100.00% | 0.96% | 34.17% |
| wholesale | keyed_noise | 100.00% | 1.02% | 40.00% |
| wholesale | primary_suppression | 96.30% | 0.00% | 0.00% |
| wholesale | raw | 100.00% | 0.00% | 100.00% |
| wholesale | rounding | 100.00% | 0.03% | 100.00% |
| wholesale | winsor_keyed | 100.00% | 11.15% | 40.00% |
| wholesale | winsor_only | 100.00% | 10.99% | 91.67% |

## Adversarial checks
**Exact margins:** In the recorded 3×6 wholesale table, 2 cells were initially flagged. An attacker using visible cells, nonnegativity and exact margins could reconstruct 2 primary cells exactly. Greedy complementary suppression added 5 suppressions; exactly recoverable primary cells afterward: 0. Margin withholding: False. This check is scoped to one two-dimensional table and the stated constraints, not arbitrary linked queries or background information.

**Repeated identical queries:** Across 200 random noise realizations, increasing repetitions from 1 to 1,000 reduced fresh-noise averaging RMSE by 31.1×. Fixed-key RMSE stayed constant. Both use the same lookup-noise distribution and scale. Fixed keys address this averaging attack only; they do not establish general confidentiality.

## Geographic strand
110 occupied half-degree grid cells from real GeoNames GB settlement coordinates. The primary symmetric 4-neighbour graph yields residual Moran's I = 0.0653, permutation p = 0.205 (199 permutations). Neighbour sensitivity k = 2/4/8 is recorded separately. These are exploratory diagnostics, without a multiple-testing claim. Point neighbours are not administrative polygon contiguity. Settlement populations can overlap and have mixed reference years; their sum is not a UK population estimate.

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
