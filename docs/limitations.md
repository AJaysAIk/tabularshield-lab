# Scope, findings and remaining work

This repository is an independently implemented, AI-assisted research prototype. It demonstrates actual software behavior and reproducible public-data experiments. It is not peer-reviewed, deployed at a statistical agency, integrated into Cantabular, or certified for confidential publication.

## Important remaining limitations

1. **Public-data analogue:** records are already public. Abalone and settlement records are not confidential human microdata. The results assess numerical behavior and stated attack models, not empirical privacy of real respondents.
2. **Proxy risk:** near-truth sensitive-cell rate is not re-identification probability or a formal disclosure-risk estimate. Exact reconstruction can remain possible even when the direct proxy looks favorable.
3. **Incomplete release protection:** the prototype has no formal differential-privacy guarantee, compositional query accounting, general linked-table reconstruction defense, zero-cell protection or robust confidential data-update policy.
4. **Illustrative lookup table:** this is not an ONS/ABS-calibrated p-table or full continuous-data CKM implementation. The lookup can return zero. Stable keys alone do not guarantee privacy.
5. **Public keys:** reference seeds and the API key are intentionally public. This enables reproducibility and makes them unsuitable for confidential deployment. Do not treat these examples as cryptographic access control.
6. **Scale restrictions:** nonnegative magnitude variables only. Negative income, survey weights, repeated contributors, longitudinal linkage and mixed-sign totals require additional modeling. No arbitrary filters or uploads are supported.
7. **Capping:** quantiles and rounding bases are computed from a fixed public snapshot. On confidential data, estimation or release of data-dependent settings needs separate protection. Capping changes the estimand and introduces bias.
8. **Suppression scope:** greedy complementarity is scoped to one 2D table, exact margins and nonnegativity. It can suppress more than necessary and does not protect all cross-table queries or background knowledge. The heuristic also knows confidential truth when choosing protection widths; the attacker does not.
9. **Geography:** half-degree grids and point-neighbour graphs are approximations. Listed places can overlap, use different reference years, and are not a non-overlapping national population census. The grid sum must not be reported as the UK population.
10. **Uncertainty:** 95% intervals quantify key-seed variability on fixed queries. No population sampling inference is claimed. Exploratory spatial sensitivity p-values are not a multiple-comparison-adjusted confirmatory claim.
11. **Operations:** API correctness and bounded inputs are tested; load, independent security assessment, production monitoring, authorization, secrets management and integration with an actual host platform are future work.
12. **Human evidence:** generated documents are training material, not proof that training was delivered. A project plan is not evidence of managing an actual two-year funded programme. Code review by an independent person has not been claimed. The author must reproduce, critique and explain the work before claiming personal competence.

## Before confidential deployment

Obtain a domain-approved threat model and policy, evaluate with representative authorized data, implement calibrated protection and composition controls, commission independent statistical/security review, verify the real platform's release rules and build a monitored operational workflow. These are substantive next stages, not labels this portfolio repository can award itself.

