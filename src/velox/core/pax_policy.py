"""Canonical guest age to pax mapping rules for reservation flows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PaxPolicy:
    """Defines age thresholds used while normalizing guest counts."""

    child_max_age: int = 16

    @property
    def adult_min_age(self) -> int:
        """Returns minimum age considered as adult."""
        return self.child_max_age + 1


@dataclass(frozen=True, slots=True)
class PaxNormalizationResult:
    """Normalized pax counts derived from raw adult count and child ages."""

    adult_count: int
    child_ages: tuple[int, ...]
    promoted_child_ages: tuple[int, ...]


def normalize_pax(
    *,
    adult_count: int,
    child_ages: list[int] | tuple[int, ...],
    policy: PaxPolicy | None = None,
) -> PaxNormalizationResult:
    """Normalizes pax counts using a canonical age policy."""
    active_policy = policy or PaxPolicy()
    kept_children: list[int] = []
    promoted_children: list[int] = []
    normalized_adults = adult_count

    for age in child_ages:
        if age >= active_policy.adult_min_age:
            normalized_adults += 1
            promoted_children.append(age)
            continue
        kept_children.append(age)

    return PaxNormalizationResult(
        adult_count=normalized_adults,
        child_ages=tuple(kept_children),
        promoted_child_ages=tuple(promoted_children),
    )

