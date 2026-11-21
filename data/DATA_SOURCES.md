# Data attribution and transformations

All evaluation inputs are publicly downloadable data. No bespoke synthetic rows were invented to generate favorable headline results. Small hand-built arrays in tests are explicitly test fixtures.

| Snapshot | Original source and attribution | Licence | Contributor unit |
|---|---|---|---|
| Wholesale | Cardoso, M. (2013). *Wholesale customers*. UCI. [DOI 10.24432/C5030X](https://doi.org/10.24432/C5030X) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Distributor customer |
| Abalone | Nash, W., Sellers, T., Talbot, S., Cawthorn, A., & Ford, W. (1994). *Abalone*. UCI. [DOI 10.24432/C55C7W](https://doi.org/10.24432/C55C7W) | CC BY 4.0 | Specimen |
| GeoNames GB | [GeoNames geographical database](https://www.geonames.org/about.html); [cities15000 export](https://download.geonames.org/export/dump/) | CC BY 4.0 | Listed settlement |

The immutable processed CSVs and their exact hashes are committed. Raw archive hashes, preparation date, URLs, row counts and transformations are recorded in [manifest.json](manifest.json). Raw archives are omitted from Git; they can change at the source. Downloading current GeoNames data may therefore produce a different snapshot. Preserve the committed processed snapshot to reproduce the reference run.

Wholesale and Abalone retain every source row. Their row-position IDs provide stable experimental contributor identities within this snapshot. Fresh spending, ring count and length are assigned fixed, documented bands. No missing-value imputation or data cleaning discards extremes. Amounts remain in source units; monetary values are not labelled pounds. Abalone weights retain their original numerical scale.

GeoNames rows are selected from the public `cities15000` dump using country `GB`, feature class `P` and population >=15,000. Stable GeoNames IDs, reported populations, coordinates, administrative codes and modification dates are retained. Half-degree bands use mathematical floor, including for negative longitude. These settlement totals may overlap or refer to different dates. They are not confidential household records or a UK population estimate.

To rebuild from downloaded source archives, run `python scripts/prepare_data.py`. That command intentionally updates the manifest and checksums; it is a data-refresh operation, not part of ordinary reproduction. Review and rerun experiments before committing changed data.
