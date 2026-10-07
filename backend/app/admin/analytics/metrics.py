"""Pure rules on top of the aggregated numbers: shares and the automatic flags.

Kept free of I/O, so the thresholds are easy to test.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class TaskFlag(StrEnum):
    OUT_OF_TARGET = "out_of_target"
    VARIANT_SPREAD = "variant_spread"
    POSSIBLE_LEAK = "possible_leak"


@dataclass(frozen=True, slots=True)
class FlagRules:
    min_attempts: int
    target_min: float
    target_max: float
    spread_pp: float
    leak_pp: float

    @classmethod
    def from_parameters(cls, values: dict[str, int]) -> "FlagRules":
        return cls(
            min_attempts=values["min_attempts_for_flags"],
            target_min=values["target_solve_min"],
            target_max=values["target_solve_max"],
            spread_pp=values["variant_spread_pp"],
            leak_pp=values["leak_jump_pp"],
        )


def share(part: int | float | None, whole: int | float | None) -> float | None:
    """Percent with one decimal; None when there is nothing to divide by."""
    if not whole:
        return None
    return round(100 * float(part or 0) / float(whole), 1)


def outcome_shares(attempts: int, full: int, partial: int, abandoned: int) -> dict[str, Any]:
    """The four outcomes of a task in an attempt. `unsolved` = answered and earned nothing."""
    unsolved = max(attempts - full - partial - abandoned, 0)
    return {
        "attempts": attempts,
        "fullShare": share(full, attempts),
        "partialShare": share(partial, attempts),
        "abandonedShare": share(abandoned, attempts),
        "unsolvedShare": share(unsolved, attempts),
    }


def task_flags(
    rules: FlagRules,
    *,
    attempts: int,
    full_share: float | None,
    variant_spread_pp: float | None,
    max_weekly_jump_pp: float | None,
) -> list[TaskFlag]:
    """Flags of one task. Below the minimum of attempts nothing is flagged: too few data.

    `variant_spread_pp` and `max_weekly_jump_pp` are already restricted to groups with enough
    attempts by the query that computed them.
    """
    if attempts < rules.min_attempts or full_share is None:
        return []
    flags = []
    if not rules.target_min <= full_share <= rules.target_max:
        flags.append(TaskFlag.OUT_OF_TARGET)
    if variant_spread_pp is not None and variant_spread_pp > rules.spread_pp:
        flags.append(TaskFlag.VARIANT_SPREAD)
    if max_weekly_jump_pp is not None and max_weekly_jump_pp > rules.leak_pp:
        flags.append(TaskFlag.POSSIBLE_LEAK)
    return flags


def invites_anomalous(
    max_per_day: int, median_per_day: float | None, factor: int, minimum: int
) -> bool:
    """A company's busiest day is far above what a typical employer sends on theirs."""
    if max_per_day < minimum or not median_per_day:
        return False
    return max_per_day > factor * median_per_day


def response_low(inbound: int, responded: int, threshold: float, minimum: int) -> bool:
    if inbound < minimum:
        return False
    value = share(responded, inbound)
    return value is not None and value < threshold
