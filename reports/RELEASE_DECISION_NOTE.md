# Release decision: what the extra suppression changes

## Decision being considered
Whether to publish the recorded Wholesale Delicassen table with primary suppression alone or with the tested additional suppressions. This is a worked public-data example for discussion with a statistical-data publisher.

## Evidence
The table has 18 cells. Primary suppression hides 2, leaving 16/18 (88.9%) visible. Exact row and column totals let an attacker recover both initially hidden cells exactly. Adding 5 suppressions leaves 11/18 (61.1%) visible: a loss of 27.8 percentage points of cell coverage. Exact recovery of primary cells falls from 2 to 0 under the recorded attacker constraints. Row and column totals remain available.

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
