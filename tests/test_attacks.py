import numpy as np
import pytest

from tabularshield.attacks import averaging_attack, complementary_suppression, linear_intervals


def test_one_hidden_cell_is_exactly_recovered():
    published = np.array([[np.nan, 20.0], [30.0, 40.0]])
    lo, hi = linear_intervals(published, np.array([30.0, 70.0]), np.array([40.0, 60.0]))
    assert lo[0, 0] == hi[0, 0] == 10.0


def test_cycle_has_nontrivial_feasible_interval():
    published = np.full((2, 2), np.nan)
    lo, hi = linear_intervals(published, np.array([30.0, 70.0]), np.array([40.0, 60.0]))
    assert lo[0, 0] == 0
    assert hi[0, 0] == 30


def test_greedy_suppression_prevents_exact_recovery_in_small_example():
    truth = np.array([[10.0, 20.0], [30.0, 40.0]])
    primary = np.array([[True, False], [False, False]])
    result = complementary_suppression(truth, primary)
    assert not result["margins_withheld"]
    assert result["mask"].sum() > primary.sum()
    assert result["upper"][0, 0] - result["lower"][0, 0] >= 2


def test_impossible_with_margins_requires_margin_withholding():
    truth = np.array([[100.0]])
    result = complementary_suppression(truth, np.array([[True]]))
    assert result["margins_withheld"]


@pytest.mark.parametrize(
    "published,rows,columns",
    [
        ([[1.0, 2.0]], [2.0], [1.0, 2.0]),
        ([[np.nan, 2.0]], [-1.0], [1.0, 2.0]),
        ([[np.nan, 2.0]], [3.0, 4.0], [1.0, 2.0]),
        ([[np.nan, 2.0]], [np.inf], [1.0, 2.0]),
    ],
)
def test_inconsistent_constraints_rejected(published, rows, columns):
    with pytest.raises(ValueError):
        linear_intervals(np.array(published), np.array(rows), np.array(columns))


def test_averaging_attack_negative_control_succeeds():
    result = averaging_attack(10.0)
    assert result[-1]["iid_rmse"] < result[0]["iid_rmse"] / 10
    assert result[-1]["fixed_key_rmse"] == result[0]["fixed_key_rmse"]


@pytest.mark.parametrize("scale,trials", [(0, 200), (-1, 200), (1, 1)])
def test_invalid_averaging_experiment_rejected(scale, trials):
    with pytest.raises(ValueError):
        averaging_attack(scale, trials=trials)
