"""Sources of the starter code tasks: statement, reference solution and test generators.

`uv run python -m app.seed.code_bank` rebuilds `data/assessment/code/*.json` from them, one file
per module; `--check` only verifies that the files are up to date. Expected outputs are never
written by hand: the builder runs the reference solution on every input and, where a task has a
slow but obvious `brute` solution, compares the two on random small inputs first.

The judge compares stdout exactly and the runner cuts it at 999 characters, so a task prints
integers or short fixed strings and packs many cases into one group. Group 0 is the open one.

Difficulty: easy is one pass over a string or an array; medium needs a standard technique
(hashing, a stack, sorting with a greedy step, BFS, a sliding window); hard needs dynamic
programming, weighted graphs or a search over the answer. Inputs are capped at 60 000 characters,
so the last hidden group of a task goes up to the limits of its statement.
"""

import contextlib
import io
import random
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Final

REFERENCE_LANGUAGE: Final = "python-3.14"
CROSS_CHECKS: Final = 25


@dataclass(frozen=True, slots=True)
class CodeTask:
    key: str
    title: str
    difficulty: str
    specializations: tuple[str, ...]
    topic: str
    statement: str
    solution: str
    # Input of the open group, the one the candidate sees and runs.
    sample: str
    # Inputs of the hidden groups, from easy edge cases to the largest one.
    hidden: Callable[[random.Random], list[str]]
    brute: str | None = None
    # A random small input for the comparison with `brute`.
    small: Callable[[random.Random], str] | None = None
    time_limit: float = 5


def pack(cases: Iterable[str]) -> str:
    """Many cases in one input: their number, then the cases."""
    rows = list(cases)
    return f"{len(rows)}\n" + "\n".join(rows) + "\n"


def run(code: str, stdin: str) -> str:
    """Stdout of a solution, executed in this process."""
    out = io.StringIO()
    previous = sys.stdin
    sys.stdin = io.StringIO(stdin)
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(code, "<solution>", "exec"), {"__name__": "__main__"})  # noqa: S102
    finally:
        sys.stdin = previous
    return out.getvalue()


def build(task: CodeTask) -> dict[str, Any]:
    """The task as a row of a `code/*.json` seed file."""
    rng = random.Random(task.key)
    if task.brute and task.small:
        for _ in range(CROSS_CHECKS):
            stdin = task.small(rng)
            fast, slow = run(task.solution, stdin), run(task.brute, stdin)
            if fast != slow:
                msg = f"{task.key}: solution and brute disagree on {stdin!r}: {fast!r} != {slow!r}"
                raise ValueError(msg)
    groups = [
        {"input": stdin, "expected": run(task.solution, stdin).strip(), "hidden": index > 0}
        for index, stdin in enumerate([task.sample, *task.hidden(rng)])
    ]
    return {
        "key": task.key,
        "title": task.title,
        "difficulty": task.difficulty,
        "specializations": list(task.specializations),
        "topic": task.topic,
        "statement": task.statement,
        "time_limit": task.time_limit,
        "reference": {"language": REFERENCE_LANGUAGE, "code": task.solution},
        "groups": groups,
    }
