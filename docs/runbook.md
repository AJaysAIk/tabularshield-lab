# Runbook

## Healthy development run
1. Install dependencies and the package in a source checkout (README).
2. Run `tabularshield validate`; compare hashes with `data/manifest.json`.
3. Run tests, evaluation and report generation.
4. Open `reports/report.html` locally. Start the optional API on localhost.

## Failure handling

| Symptom | Investigation | Recovery |
|---|---|---|
| Checksum mismatch | Did source preparation or an accidental edit change the snapshot? | Restore the committed data or explicitly review a new snapshot, manifest and results |
| LP infeasible | Inconsistent margins, negative values, schema mismatch or numerical scaling | Recheck released constraints; do not label an infeasible solve as safe |
| Large distortion | Dominance, sparse partitions, capping bias or excessive noise scale | Inspect profiles and ablations; consult the intended utility requirement |
| Undefined risk/error | Empty denominator, full withholding or constant spatial field | Report N/A and explain it; never silently replace with a favorable zero |
| API validation error | Unsupported measure/dimension, extra seed/filter or duplicate grouping | Correct request; do not loosen the public-data boundary |
| Stale API data | Dataset cache persists for process lifetime | Restart after controlled snapshot review |
| Import issue after editable install on macOS | Hidden `.pth` file may be ignored by Python | Reinstall normally, or use `PYTHONPATH=src python -m tabularshield` from checkout; do not change system Python |

## Release checklist
Confirm dataset attribution and checksums; run verification; inspect all negative controls; review limitations and changed parameters; regenerate reports from the intended commit. Never commit credentials or private client data. Pin dependencies for a reference run, and test upgrades through CI before accepting changed numerical results.

## Source refresh
`scripts/prepare_data.py` is an explicit refresh step. The GeoNames upstream archive changes. Ordinary reproduction uses the committed processed CSVs. Retain the previous snapshot and results when comparing versions. No data-refresh command is run by the public API.

