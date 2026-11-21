# Verification strategy

Tests target mathematical behavior and plausible failures, not just examples of calling functions.

| Boundary | Evidence |
|---|---|
| Statistical correctness | Hand-calculated totals, maxima, dominance, centered lookup distribution |
| Contributor consistency | Row reordering and equivalent grouping shapes preserve output |
| Magnitude bounds | Hypothesis-generated nonnegative contributors test release nonnegativity and noise bound |
| Bad input | Duplicate IDs, missing values, NaN, infinity, negative magnitudes and invalid policy rejection |
| Reconstruction | Exact one-cell recovery, nontrivial 2D cycles, infeasible margins and complementary suppression |
| Averaging attack | Fresh-noise baseline becomes easier to estimate while fixed-noise error remains constant |
| API contract | Read-only public datasets, stable equivalent queries, allowlists and no raw diagnostic fields |
| Data integrity | Real file hashes and a deliberately modified copied snapshot |
| Geography | Hand-calculated Moran's I, constant-field behavior, graph symmetry and seeded permutations |
| Pipeline | Complete method grid, baseline identities, interval-width checks and report generation |
| Reproducibility | Full 30-seed rerun compared with committed CSV/JSON evidence |

Run `pytest --cov=tabularshield --cov-report=term-missing`. Coverage is diagnostic, not an objective to inflate by testing trivial lines. The CI matrix checks Python 3.12 and 3.14. No confidential-data safety claim follows from a green build.

Future checks before production include independent statistical review, multi-table attack suites, background-knowledge assumptions, load tests, controlled data refresh, authorized security testing and integration with the actual host's contracts.

