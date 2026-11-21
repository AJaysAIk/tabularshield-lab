import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tabularshield.core import Policy, aggregate, metrics, ptable, record_keys, release


@pytest.fixture
def frame():
    return pd.DataFrame(
        {
            "unit_id": ["a", "b", "c", "d"],
            "group": ["A", "A", "B", "B"],
            "same": ["all"] * 4,
            "amount": [10.0, 20.0, 30.0, 40.0],
        }
    )


def test_hand_calculated_aggregation(frame):
    table = aggregate(frame, ("group",), "amount", b"x", "fixed")
    assert table.truth.tolist() == [30.0, 70.0]
    assert table.max_value.tolist() == [20.0, 40.0]
    assert table["count"].tolist() == [2, 2]
    assert table.unsafe.tolist() == [True, True]
    assert table.top2_share.tolist() == [1.0, 1.0]


def test_keys_and_release_stable_under_row_reordering(frame):
    a = aggregate(frame, ("group",), "amount", b"x", "fixed")
    b = aggregate(frame.sample(frac=1, random_state=6), ("group",), "amount", b"x", "fixed")
    pd.testing.assert_frame_equal(a, b)
    np.testing.assert_array_equal(release(a, "keyed_noise"), release(b, "keyed_noise"))


def test_identical_contributors_across_query_shapes_have_same_noise(frame):
    a = aggregate(frame, ("group",), "amount", b"x", "fixed")
    b = aggregate(frame, ("same", "group"), "amount", b"x", "fixed")
    np.testing.assert_array_equal(a.cell_key, b.cell_key)
    np.testing.assert_array_equal(release(a, "keyed_noise"), release(b, "keyed_noise"))


def test_different_secret_changes_keys():
    assert not np.array_equal(record_keys(range(50), b"x", "a"), record_keys(range(50), b"y", "a"))


def test_lookup_is_centered_over_entire_key_space():
    distribution = ptable(np.arange(4096))
    assert distribution.mean() == 0
    assert distribution.var() == 0.375
    assert (distribution == 0).mean() == 0.25


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_count": 0},
        {"min_count": True},
        {"delta": 0},
        {"delta": 0.51},
        {"delta": float("nan")},
        {"cap_quantile": 0},
        {"dominance_threshold": 1.1},
    ],
)
def test_invalid_policy_rejected(kwargs):
    with pytest.raises(ValueError):
        Policy(**kwargs)


@pytest.mark.parametrize("change", ["duplicate", "negative", "nan", "infinite", "missing_group"])
def test_invalid_inputs_rejected(frame, change):
    if change == "duplicate":
        frame.loc[1, "unit_id"] = "a"
    elif change == "missing_group":
        frame.loc[0, "group"] = None
    else:
        frame.loc[0, "amount"] = {"negative": -1.0, "nan": np.nan, "infinite": np.inf}[change]
    with pytest.raises(ValueError):
        aggregate(frame, ("group",), "amount", b"x", "n")


def test_invalid_grouping_and_secret(frame):
    for dimensions in [(), ("group", "group"), ("unknown",), ("amount",)]:
        with pytest.raises(ValueError):
            aggregate(frame, dimensions, "amount", b"x", "n")
    with pytest.raises(ValueError):
        record_keys([1], b"", "n")


def test_zero_totals_and_full_suppression(frame):
    frame.amount = 0.0
    table = aggregate(frame, ("group",), "amount", b"x", "n")
    np.testing.assert_array_equal(release(table, "keyed_noise"), [0.0, 0.0])
    result = metrics(table, release(table, "primary_suppression"))
    assert result["coverage"] == 0
    assert result["wape_visible"] is None


def test_no_unsafe_cells_returns_undefined_risk(frame):
    table = aggregate(
        frame, ("group",), "amount", b"x", "n", Policy(min_count=1, dominance_threshold=1)
    )
    assert metrics(table, release(table, "raw"))["sensitive_near_truth_rate"] is None


def test_masking_is_not_reported_as_zero_error(frame):
    table = aggregate(frame, ("group",), "amount", b"x", "n")
    result = metrics(table, release(table, "primary_suppression"))
    assert result["coverage"] == 0
    assert result["mae_visible"] is None
    assert result["sensitive_near_truth_rate"] == 0


def test_unknown_method_and_invalid_rounding(frame):
    table = aggregate(frame, ("group",), "amount", b"x", "n")
    with pytest.raises(ValueError):
        release(table, "unimplemented")
    with pytest.raises(ValueError):
        release(table, "rounding", rounding_base=0)
    with pytest.raises(ValueError):
        release(table, "iid_noise")


@given(
    st.lists(
        st.floats(min_value=0, max_value=1e7, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=40,
    )
)
@settings(max_examples=70, deadline=None)
def test_nonnegative_and_bounded_noise_for_arbitrary_contributions(values):
    frame = pd.DataFrame({"unit_id": [str(i) for i in range(len(values))], "g": "all", "x": values})
    table = aggregate(frame, ("g",), "x", b"property-test", "n")
    for delta in [0.05, 0.2, 0.5]:
        policy = Policy(delta=delta)
        protected = release(table, "keyed_noise", policy)
        assert protected[0] >= 0
        assert abs(protected[0] - table.truth.iloc[0]) <= delta * max(values) + 1e-6
