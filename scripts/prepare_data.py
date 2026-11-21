"""Prepare locally downloaded, openly licensed source snapshots; no private data."""

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data/raw", ROOT / "data/processed"
OUT.mkdir(parents=True, exist_ok=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


with ZipFile(RAW / "wholesale.zip") as z:
    wholesale = pd.read_csv(io.BytesIO(z.read("Wholesale customers data.csv")))
wholesale.insert(0, "unit_id", [f"wholesale-{i:04}" for i in range(len(wholesale))])
# Fixed cut-points, not fitted to maximize any experimental result.
wholesale["spend_band"] = pd.cut(
    wholesale.Fresh, [-1, 5000, 15000, np.inf], labels=["low", "medium", "high"]
).astype(str)
wholesale.to_csv(OUT / "wholesale.csv", index=False)

with ZipFile(RAW / "abalone.zip") as z:
    abalone = pd.read_csv(
        io.BytesIO(z.read("abalone.data")),
        header=None,
        names=[
            "Sex",
            "Length",
            "Diameter",
            "Height",
            "Whole_weight",
            "Shucked_weight",
            "Viscera_weight",
            "Shell_weight",
            "Rings",
        ],
    )
abalone.insert(0, "unit_id", [f"abalone-{i:05}" for i in range(len(abalone))])
abalone["ring_band"] = pd.cut(
    abalone.Rings, [-1, 7, 10, 15, np.inf], labels=["0-7", "8-10", "11-15", "16+"]
).astype(str)
abalone["length_band"] = pd.cut(
    abalone.Length, [-1, 0.4, 0.6, np.inf], labels=["small", "medium", "large"]
).astype(str)
abalone.to_csv(OUT / "abalone.csv", index=False)

records = []
with ZipFile(RAW / "cities15000.zip") as z:
    for row in csv.reader(io.StringIO(z.read("cities15000.txt").decode("utf-8")), delimiter="\t"):
        if row[8] == "GB" and row[6] == "P" and int(row[14]) >= 15000:
            records.append(
                {
                    "unit_id": "geonames-" + row[0],
                    "name": row[1],
                    "latitude": float(row[4]),
                    "longitude": float(row[5]),
                    "admin1": row[10],
                    "population": int(row[14]),
                    "source_modified": row[18],
                }
            )
geo = pd.DataFrame(records).sort_values("unit_id").reset_index(drop=True)
geo["lat_band"] = np.floor(geo.latitude * 2).astype(int).astype(str)
geo["lon_band"] = np.floor(geo.longitude * 2).astype(int).astype(str)
geo.to_csv(OUT / "geonames_gb.csv", index=False)

entries = {
    "wholesale": {
        "source": "https://archive.ics.uci.edu/dataset/292/wholesale+customers",
        "download": "https://archive.ics.uci.edu/static/public/292/wholesale%2Bcustomers.zip",
        "citation": "Cardoso, M. (2013). Wholesale customers. UCI. DOI:10.24432/C5030X.",
        "unit": "one distributor customer; amounts in source monetary units, not assumed GBP",
        "transformations": "Stable row-position IDs; fixed Fresh spend bands; no row removal or outlier trimming.",
        "measures": ["Fresh", "Milk", "Grocery", "Frozen", "Detergents_Paper", "Delicassen"],
        "dimensions": ["Region", "Channel", "spend_band"],
        "workloads": [["Region"], ["Region", "Channel"], ["Region", "Channel", "spend_band"]],
        "archive": "wholesale.zip",
        "filename": "wholesale.csv",
        "rows": len(wholesale),
    },
    "abalone": {
        "source": "https://archive.ics.uci.edu/dataset/1/abalone",
        "download": "https://archive.ics.uci.edu/static/public/1/abalone.zip",
        "citation": "Nash, W., Sellers, T., Talbot, S., Cawthorn, A., & Ford, W. (1994). Abalone. UCI. DOI:10.24432/C55C7W.",
        "unit": "one abalone specimen; weights retained on source scale",
        "transformations": "Stable row-position IDs; fixed ring/length bands; no imputation or row removal.",
        "measures": ["Whole_weight", "Shell_weight"],
        "dimensions": ["Sex", "ring_band", "length_band"],
        "workloads": [["Sex"], ["Sex", "ring_band"], ["Sex", "ring_band", "length_band"]],
        "archive": "abalone.zip",
        "filename": "abalone.csv",
        "rows": len(abalone),
    },
    "geonames_gb": {
        "source": "https://download.geonames.org/export/dump/",
        "download": "https://download.geonames.org/export/dump/cities15000.zip",
        "citation": "GeoNames geographical database, downloaded snapshot; CC BY 4.0. https://www.geonames.org/about.html",
        "unit": "one listed populated place, NOT a person or household; populations can overlap and have different reference dates",
        "transformations": "GB, feature class P, reported population >=15,000; sort by geoname ID; fixed 0.5-degree grid bins.",
        "measures": ["population"],
        "dimensions": ["admin1", "lat_band", "lon_band"],
        "workloads": [["admin1"], ["lat_band", "lon_band"], ["admin1", "lat_band", "lon_band"]],
        "archive": "cities15000.zip",
        "filename": "geonames_gb.csv",
        "rows": len(geo),
    },
}
for item in entries.values():
    item["license"] = "CC BY 4.0"
    item["sha256"] = digest(OUT / item["filename"])
    item["archive_sha256"] = digest(RAW / item["archive"])
    item["prepared_utc"] = datetime.now(timezone.utc).isoformat()
(ROOT / "data/manifest.json").write_text(json.dumps(entries, indent=2) + "\n")
print(
    json.dumps(
        {key: {"rows": value["rows"], "sha256": value["sha256"]} for key, value in entries.items()},
        indent=2,
    )
)
