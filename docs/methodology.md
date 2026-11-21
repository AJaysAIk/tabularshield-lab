# Methods and threat model

## Unit and table definition

A contributor occurs once per input dataset. Repeated records require upstream unit aggregation; duplicates are rejected here. A query partitions contributors by one to three approved categorical dimensions and reports their magnitude sum. Only occupied cells are enumerated; that presence information is itself a limitation. Counts, maxima, flags and keys are internal evaluation fields, not API outputs.

The public data represent customers, abalone specimens and settlements respectively. The last two are numerical analogues, not evidence about confidential people. Missing, negative or nonfinite target values are rejected. All original rows are retained. Extreme observations are intentionally retained in truth; only the explicit winsorisation comparators cap them.

## Sensitivity indicator

Flag a cell when it contains fewer than five contributors **or** its two largest values exceed 85% of its total. Zero totals have a dominance share of zero. Thresholds are research settings, not agency-approved policy. Risk changes with the query dimensions, and contributor background knowledge is not captured by this rule.

## Comparators

| Method | Operation | Main weakness to investigate |
|---|---|---|
| Raw | Exact sum | Full disclosure of flagged totals |
| Primary suppression | Withhold flagged cells | Exact margins or linked tables may reconstruct them |
| Rounding | Round to a fixed magnitude-specific base | Predictable error bounds; little distortion for large cells |
| Winsor only | Globally cap contributions at the 95th percentile | Downward bias; small values remain exact |
| IID noise | Fresh lookup noise on each query | Averaging repeated releases reduces error |
| Keyed noise | Stable contributor-key sum chooses lookup noise | Composition and background knowledge remain unsolved |
| Winsor + keyed | Capping followed by keyed perturbation | Bias plus noise; not automatically better |

### Keyed magnitude prototype

HMAC-SHA256 maps a contributor ID to a fixed record key in `[0,4095]`, namespaced by the data digest and measure. A cell key is the modular sum of its record keys. The lookup distribution has values `[-1,-0.5,0,0.5,1]` with probabilities `[1/8,1/4,1/4,1/4,1/8]`. It is symmetric with mean zero and variance 0.375. This illustrative distribution was chosen for auditability, not calibrated disclosure protection.

For total `T`, largest contribution `M`, scale `d` and lookup value `v`, output `T + d*M*v`. With `0<d<=0.5`, `M<=T` and `|v|<=1`, the result is nonnegative without clipping. Capped experiments use capped `T` and `M`. Matching contributor sets obtain consistent perturbations within the same data/measure/key context, regardless of grouping labels or row order. Different dataset versions deliberately have different contexts. Public experiment seeds are not secrets.

The magnitude scaling follows the general concept described in the [SDC Handbook, section 4.6](https://sdctools.github.io/HandbookSDC/04-magnitude-tabular-data.html). This prototype omits official p-table calibration and small-magnitude interpolation. It is not a full CKM replication. The source's role is conceptual; code is independently written.

## What the metrics mean

- **Coverage:** published cells / occupied cells. Suppression is not silently imputed to zero.
- **Visible WAPE:** sum of absolute errors / sum of original values, considering published cells only.
- **Visible MAE:** mean absolute error on published cells, in the source measure's units.
- **Retained truth share:** original value in published cells / all original value. It is not the signed bias in released values.
- **Sensitive near-truth rate:** proportion of originally flagged cells with visible outputs within 5% of truth. Hidden outputs count as not directly near truth. This is a diagnostic proxy, **not a privacy probability**; the margin attack demonstrates its blind spot.
- **Unchanged visible rate:** fraction of published values numerically equal to truth.

Undefined denominators remain missing, not zero. We publish seed-level macro means of the fixed queries, not an unsupported population estimate. Paired contrasts compare capped and uncapped perturbation using the same record-key seed. Intervals use 30 seed means; repeated cells are not counted as independent statistical samples.

## Attacks

1. **Reconstruction:** an adversary sees exact released cells and exact row/column margins of a single 2D table. Two linear programs per hidden cell bound its feasible nonnegative value. An interval of effectively zero width means exact recovery in this model. Truth is not supplied as an attacker bound. Greedy complementary suppression keeps adding low-value visible cells until original sensitive-cell intervals meet the stated width target; it may oversuppress. If even full cell withholding fails, exact margins must also be withheld. There is no optimality claim.
2. **Averaging:** compare fresh noise and fixed noise using the same lookup distribution and scale over 200 realizations. Estimate RMSE after 1/10/100/1000 repetitions. Stability defeats this particular averaging attack; it is not a general reconstruction defense.

## Geographic strand

Aggregate real GeoNames GB settlement records into occupied half-degree cells. Evaluate relative errors with symmetric binary k-nearest-neighbour graphs ordered by great-circle distance. Moran's I and two-sided permutation diagnostics describe spatial residual patterns. Primary k=4, sensitivity k=2/8, 199 permutations. These exploratory results do not establish absence of spatial leakage. Centroid graphs do not reproduce boundary contiguity. No confidential household locations are used.

## Primary references

- [Cantabular: magnitude tables](https://cantabular.com/blog/protecting-magnitude-tables-with-cantabular): relevant product problem and methods context, not an endorsement.
- [Cantabular: Python cell-key introduction](https://cantabular.com/blog/demonstrating-cell-key-perturbation-in-python): frequency-table starting point; this work is an independent magnitude-table experiment.
- [ONS comparison of post-tabular methods](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/methodologies/comparisonofposttabularstatisticaldisclosurecontrolmethods): frequency-table risk/utility context; our results do not replicate its study.
- [SDC Handbook](https://sdctools.github.io/HandbookSDC/04-magnitude-tabular-data.html): magnitude-table concepts and disclosure-control background.

