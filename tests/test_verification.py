import pytest

from tabularshield.verification import compare_nested


def test_last_bit_numerical_difference_is_accepted():
    compare_nested(
        {"moran_i": 0.06529107495406021, "count": 2}, {"moran_i": 0.06529107495406022, "count": 2}
    )


@pytest.mark.parametrize(
    "expected,actual",
    [
        ({"count": 2}, {"count": 3}),
        ({"count": 2}, {"count": 2.0}),
        ({"safe": False}, {"safe": 0}),
        ({"method": "raw"}, {"method": "noise"}),
        ({"moran_i": 0.06}, {"moran_i": 0.07}),
        ([1.0, 2.0], [1.0]),
        ({"value": 1.0}, {"other": 1.0}),
        ({"value": 1.0}, {"value": float("nan")}),
    ],
)
def test_substantive_or_structural_changes_are_rejected(expected, actual):
    with pytest.raises(AssertionError):
        compare_nested(expected, actual)
