"""Pinned public datasets with strict validation and explicit contributor units."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Dataset:
    name: str
    frame: pd.DataFrame
    measures: tuple[str, ...]
    dimensions: tuple[str, ...]
    workloads: tuple[tuple[str, ...], ...]
    digest: str


def validate(frame: pd.DataFrame, measures: tuple[str, ...], dimensions: tuple[str, ...]) -> None:
    required = ["unit_id", *measures, *dimensions]
    if not set(required).issubset(frame.columns):
        raise ValueError("Missing required columns")
    if frame.empty or frame[required].isna().any().any():
        raise ValueError("Empty data or missing required values")
    if frame.unit_id.duplicated().any():
        raise ValueError("Each contributor must occur once; aggregate repeated units first")
    for measure in measures:
        values = frame[measure].to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("Measures must be finite and nonnegative")
    if {"latitude", "longitude"}.issubset(frame.columns):
        if (
            not frame.latitude.between(-90, 90).all()
            or not frame.longitude.between(-180, 180).all()
        ):
            raise ValueError("Invalid WGS84 coordinates")


def load_dataset(name: str, root: Path = ROOT) -> Dataset:
    manifest = json.loads((root / "data/manifest.json").read_text())
    if name not in manifest:
        raise ValueError("Unknown dataset")
    item = manifest[name]
    path = root / "data/processed" / item["filename"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != item["sha256"]:
        raise ValueError("Dataset checksum mismatch")
    frame = pd.read_csv(path, dtype={x: str for x in ["unit_id", *item["dimensions"]]})
    measures, dimensions = tuple(item["measures"]), tuple(item["dimensions"])
    validate(frame, measures, dimensions)
    if len(frame) != item["rows"]:
        raise ValueError("Dataset row count mismatch")
    return Dataset(
        name, frame, measures, dimensions, tuple(tuple(x) for x in item["workloads"]), digest
    )
