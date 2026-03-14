from velox.core.pax_policy import PaxPolicy, normalize_pax


def test_normalize_pax_promotes_17_and_above_to_adult() -> None:
    result = normalize_pax(adult_count=2, child_ages=[4, 16, 17, 18], policy=PaxPolicy())

    assert result.adult_count == 4
    assert result.child_ages == (4, 16)
    assert result.promoted_child_ages == (17, 18)


def test_normalize_pax_respects_custom_child_age_threshold() -> None:
    result = normalize_pax(adult_count=2, child_ages=[12, 13], policy=PaxPolicy(child_max_age=12))

    assert result.adult_count == 3
    assert result.child_ages == (12,)
    assert result.promoted_child_ages == (13,)

