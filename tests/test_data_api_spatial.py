import shutil

import numpy as np
import pytest
from fastapi.testclient import TestClient

from tabularshield.api import app
from tabularshield.data import ROOT, load_dataset, validate
from tabularshield.spatial import moran_i, permutation_test, weights

client = TestClient(app)


@pytest.mark.parametrize(
    "name,rows", [("wholesale", 440), ("abalone", 4177), ("geonames_gb", None)]
)
def test_public_data_hashes_and_validity(name, rows):
    data = load_dataset(name)
    assert len(data.digest) == 64
    assert len(data.frame) == rows if rows else len(data.frame) > 100


def test_modified_data_is_rejected(tmp_path):
    shutil.copytree(ROOT / "data", tmp_path / "data")
    path = tmp_path / "data/processed/wholesale.csv"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="checksum"):
        load_dataset("wholesale", tmp_path)


def test_missing_or_duplicate_unit_rejected():
    data = load_dataset("wholesale")
    frame = data.frame.copy()
    frame.loc[0, "unit_id"] = frame.loc[1, "unit_id"]
    with pytest.raises(ValueError):
        validate(frame, data.measures, data.dimensions)


def test_api_metadata_and_health():
    assert client.get("/health").status_code == 200
    assert len(client.get("/datasets").json()) == 3


def test_api_is_deterministic_and_has_no_raw_diagnostics():
    query = {"dataset": "wholesale", "measure": "Fresh", "group_by": ["Region", "Channel"]}
    response = client.post("/query", json=query)
    assert response.status_code == 200
    assert response.json() == client.post("/query", json=query).json()
    query["group_by"] = ["Channel", "Region"]
    assert response.json() == client.post("/query", json=query).json()
    assert len(response.json()["cells"]) == 6
    for cell in response.json()["cells"]:
        assert set(cell) == {"Region", "Channel", "value"}


@pytest.mark.parametrize(
    "payload,status",
    [
        ({"dataset": "../../etc", "measure": "Fresh", "group_by": ["Region"]}, 404),
        ({"dataset": "wholesale", "measure": "secret", "group_by": ["Region"]}, 422),
        ({"dataset": "wholesale", "measure": "Fresh", "group_by": []}, 422),
        ({"dataset": "wholesale", "measure": "Fresh", "group_by": ["Region", "Region"]}, 422),
        ({"dataset": "wholesale", "measure": "Fresh", "group_by": ["unit_id"]}, 422),
        ({"dataset": "wholesale", "measure": "Fresh", "group_by": ["Region"], "seed": 7}, 422),
    ],
)
def test_api_rejects_unbounded_or_unknown_inputs(payload, status):
    assert client.post("/query", json=payload).status_code == status


def test_moran_hand_calculation():
    adjacency = np.ones((3, 3)) - np.eye(3)
    assert moran_i(np.array([1.0, 2.0, 3.0]), adjacency) == pytest.approx(-0.5)


def test_constant_spatial_field_is_undefined():
    assert moran_i(np.ones(3), np.ones((3, 3)) - np.eye(3)) is None


def test_graph_has_no_self_edges_and_is_symmetric():
    points = np.array([[54.0, -6.0], [55.0, -6.0], [54.0, -7.0], [56.0, -5.0]])
    graph = weights(points, 2)
    assert np.diag(graph).sum() == 0
    np.testing.assert_array_equal(graph, graph.T)
    assert graph.sum() >= 8


def test_spatial_permutation_is_reproducible():
    graph = np.ones((4, 4)) - np.eye(4)
    values = np.array([1.0, 2.0, 4.0, 5.0])
    result = permutation_test(values, graph, permutations=19)
    assert result == permutation_test(values, graph, permutations=19)
    assert 0.05 <= result["p_two_sided"] <= 1


@pytest.mark.parametrize(
    "coordinates,k", [([[1.0, 2.0]], 1), ([[1.0, np.nan], [2.0, 3.0]], 1), ([[1.0, 2.0, 3.0]], 1)]
)
def test_invalid_graph_rejected(coordinates, k):
    with pytest.raises(ValueError):
        weights(np.array(coordinates), k)
