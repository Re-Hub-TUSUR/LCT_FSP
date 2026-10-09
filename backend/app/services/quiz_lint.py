"""Does the right option of a choice question give itself away by its length?

A candidate who knows nothing still picks the longest option far more often than chance. The
bank is checked two ways, on the options as written: the right option may be at most
`MAX_RATIO` times as long as the average wrong one, and across a bank it may be strictly the
longest in at most `MAX_LONGEST_SHARE` of the questions. A question with several right options
is judged by their average length.
"""

from collections.abc import Iterable, Sequence
from statistics import fmean
from typing import Final

MAX_RATIO: Final = 1.3
MAX_LONGEST_SHARE: Final = 0.3


# The right option of a question, or all of them when several are right.
Right = str | Sequence[str]


def _lengths(correct: Right) -> list[int]:
    return [len(correct)] if isinstance(correct, str) else [len(option) for option in correct]


def length_ratio(correct: Right, wrong: Sequence[str]) -> float:
    """Length of the right option relative to the average wrong one; 1 = equally long."""
    return fmean(_lengths(correct)) / fmean(len(option) for option in wrong)


def is_longest(correct: Right, wrong: Sequence[str]) -> bool:
    return min(_lengths(correct)) > max(len(option) for option in wrong)


def option_warning(correct: Right, wrong: Sequence[str]) -> str | None:
    """What to fix in one question, None when the lengths do not give the answer away."""
    if not wrong or not correct:
        return None
    ratio = length_ratio(correct, wrong)
    if ratio > MAX_RATIO:
        return (
            f"Правильный ответ длиннее неверных в {ratio:.1f} раза (допустимо до {MAX_RATIO}): "
            "сделайте неверные варианты такой же длины и детальности"
        )
    return None


def longest_share(questions: Iterable[tuple[Right, Sequence[str]]]) -> float:
    """Share of questions whose right option is strictly the longest, (right, wrong) pairs."""
    flags = [is_longest(correct, wrong) for correct, wrong in questions if wrong]
    return sum(flags) / len(flags) if flags else 0.0
