"""Bounded public-data integration demo. Does not accept confidential uploads."""

import hashlib
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from .core import Policy, aggregate, release
from .data import ROOT, load_dataset

app = FastAPI(
    title="TabularShield public-data demo",
    version="0.1.0",
    description="Research integration only. No formal privacy guarantee or Cantabular affiliation.",
)


class Query(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset: str
    measure: str
    group_by: list[str] = Field(min_length=1, max_length=3)


@app.get("/", include_in_schema=False)
def research_report():
    return FileResponse(ROOT / "reports/report.html", media_type="text/html")


@lru_cache(maxsize=3)
def dataset(name):
    return load_dataset(name)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0", "scope": "public-data research demo"}


@app.get("/datasets")
def datasets():
    return [
        {
            "name": x,
            "measures": dataset(x).measures,
            "dimensions": dataset(x).dimensions,
            "sha256": dataset(x).digest,
        }
        for x in ["wholesale", "abalone", "geonames_gb"]
    ]


@app.post("/query")
def query(request: Query):
    if request.dataset not in {"wholesale", "abalone", "geonames_gb"}:
        raise HTTPException(404, "Unknown public dataset")
    source = dataset(request.dataset)
    if (
        request.measure not in source.measures
        or not set(request.group_by).issubset(source.dimensions)
        or len(set(request.group_by)) != len(request.group_by)
    ):
        raise HTTPException(422, "Invalid measure or grouping dimensions")
    # Fixed public research key/config; clients cannot choose seeds or noise levels.
    dimensions = tuple(sorted(request.group_by))
    table = aggregate(
        source.frame,
        dimensions,
        request.measure,
        b"PUBLIC-DEMO-KEY-v1",
        source.digest + ":" + request.measure,
    )
    if len(table) > 1000:
        raise HTTPException(422, "Query exceeds cell limit")
    protected = release(table, "keyed_noise", Policy())
    cells = [
        {**{d: str(row[d]) for d in dimensions}, "value": float(value)}
        for (_, row), value in zip(table.iterrows(), protected, strict=True)
    ]
    signature = hashlib.sha256(
        f"{source.digest}:{request.measure}:{dimensions}:v1".encode()
    ).hexdigest()
    # Deliberately exclude exact counts, keys, maxima, truth and risk flags.
    return {
        "dataset_sha256": source.digest,
        "query_id": signature,
        "method": "keyed_magnitude_prototype",
        "warning": "Public-data prototype; linked-query privacy is not certified.",
        "cells": cells,
    }
