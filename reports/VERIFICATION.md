# Verification record

- Python reference environment: 3.14.3.
- Local automated tests: 66 passed, including a property test over generated contributor arrays and an end-to-end public-data/API/report suite.
- Measured whole-package statement coverage: 91.3% in that run. Coverage is not a proof of statistical confidentiality.
- Lint checks passed; source and wheel builds completed. Evaluation is supported from the repository checkout with its pinned public data. Container recipe is provided but has not been run locally.
- Independent full rerun: passed, 30 seeds, 8 CSV/JSON numerical files compared.
- Reference and rerun SHA-256 for experiment_results.csv: `3122940b062fd8248f44172e611694b15dda7b6689e3010623a9adeed1b38191` (identical).
- Cross-platform verification uses relative/absolute float tolerances of 1e-10; discrete counts, schema and categories remain exact. Local reference hashes match byte-for-byte.
- Original data row counts and hashes verified against the committed manifest.
- GitHub CI status should be checked on the repository Actions page; this record does not predeclare a remote result.

One local warning notes that the installed Starlette release deprecates its httpx TestClient adapter. Tests pass; update the adapter under CI when changing that dependency.

No confidential-data release, external peer review, production load test, live Cantabular integration or client delivery is claimed.
