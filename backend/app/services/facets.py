"""Counts next to filter options: how many results a click would leave.

An item counts for a changed group G when it passes every other group and passes G after the
change, which is exactly what the list shows after the click. Failed groups are computed once per
item, so a count re-checks only the items that pass everything except, at most, G.
"""

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping
from typing import Final, Protocol

from app.schemas.facets import OptionCount
from app.services.matching import normalize_term

MAX_RELAXATIONS: Final = 3


class FacetCounter[Item, Query, Group: str]:
    def __init__(
        self,
        items: Iterable[Item],
        query: Query,
        *,
        groups: tuple[Group, ...],
        check: Callable[[Group, Item, Query], bool],
    ) -> None:
        self._check = check
        # Items passing every filter: the list itself.
        self.matching: list[Item] = []
        self._failing_only: dict[Group, list[Item]] = {group: [] for group in groups}
        for item in items:
            failed = [group for group in groups if not check(group, item, query)]
            if not failed:
                self.matching.append(item)
            elif len(failed) == 1:
                self._failing_only[failed[0]].append(item)

    @property
    def count(self) -> int:
        return len(self.matching)

    def count_with(self, group: Group, changed: Query) -> int:
        """Results once `changed` replaces the query; it differs from it in `group` only."""
        candidates = (*self.matching, *self._failing_only[group])
        return sum(self._check(group, item, changed) for item in candidates)


def spellings(values: Iterable[str]) -> dict[str, str]:
    """Normalised term → its most common spelling, e.g. `postgresql` → `PostgreSQL`."""
    seen: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for value in values:
        if value.strip():
            seen[normalize_term(value.strip())][value.strip()] += 1
    return {
        term: min(counts.items(), key=lambda item: (-item[1], item[0]))[0]
        for term, counts in seen.items()
    }


def ranked(counts: Mapping[str, int], labels: Mapping[str, str]) -> list[OptionCount]:
    """Every labelled term with its count (normalised keys), the most frequent first."""
    options = [
        OptionCount(value=label, count=counts.get(term, 0)) for term, label in labels.items()
    ]
    return sorted(options, key=lambda option: (-option.count, option.value.casefold()))


class _Counted(Protocol):
    @property
    def count(self) -> int: ...


def best_relaxations[R: _Counted](options: Iterable[R]) -> list[R]:
    """The loosenings that bring results back, the most rewarding first (stable for ties)."""
    helpful = [option for option in options if option.count > 0]
    return sorted(helpful, key=lambda option: -option.count)[:MAX_RELAXATIONS]
