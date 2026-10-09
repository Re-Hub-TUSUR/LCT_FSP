"""Deliberately wrong or too slow solutions of code tasks whose tests were once too weak.

`test_hidden_groups_reject_weak_solutions` runs each of them against the hidden groups of its
task: none may pass them all. When a task gets new tests, add the shortcut that used to pass.
Python 3 programs that read stdin like the reference solutions do. Never shown to candidates.
"""

from typing import Final

WEAK_SOLUTIONS: Final[dict[str, dict[str, str]]] = {
    "maze": {
        # Finds out only whether the exit is reachable and prints the length of a straight path.
        "manhattan_if_reachable": r"""
import sys
from collections import deque
L = sys.stdin.read().split("\n"); p = 1
for _ in range(int(L[0])):
    h, w = map(int, L[p].split()); g = L[p + 1:p + 1 + h]; p += 1 + h
    seen = {(0, 0)}; q = deque([(0, 0)])
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and g[ny][nx] == "." and (ny, nx) not in seen:
                seen.add((ny, nx)); q.append((ny, nx))
    print(h + w - 2 if (h - 1, w - 1) in seen else -1)
""",
        # Walks only right and down, so it never takes a detour.
        "right_and_down_only": r"""
import sys
L = sys.stdin.read().split("\n"); p = 1
for _ in range(int(L[0])):
    h, w = map(int, L[p].split()); g = L[p + 1:p + 1 + h]; p += 1 + h
    INF = 10 ** 9
    d = [[INF] * w for _ in range(h)]; d[0][0] = 0
    for y in range(h):
        for x in range(w):
            if g[y][x] != ".":
                continue
            if y and d[y - 1][x] < INF: d[y][x] = min(d[y][x], d[y - 1][x] + 1)
            if x and d[y][x - 1] < INF: d[y][x] = min(d[y][x], d[y][x - 1] + 1)
    print(d[h - 1][w - 1] if d[h - 1][w - 1] < INF else -1)
""",
        # Depth-first search: finds a path, not the shortest one.
        "depth_first_first_path": r"""
import sys
L = sys.stdin.read().split("\n"); p = 1
for _ in range(int(L[0])):
    h, w = map(int, L[p].split()); g = L[p + 1:p + 1 + h]; p += 1 + h
    seen = set(); st = [(0, 0, 0)]; ans = -1
    while st:
        y, x, d = st.pop()
        if (y, x) in seen:
            continue
        seen.add((y, x))
        if (y, x) == (h - 1, w - 1):
            ans = d; break
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and g[ny][nx] == "." and (ny, nx) not in seen:
                st.append((ny, nx, d + 1))
    print(ans)
""",
    },
    "edit-distance": {
        # Correct, but exponential: only the short inputs let it finish.
        "recursion_without_memo": r"""
import sys
sys.setrecursionlimit(10000)
L = sys.stdin.read().split("\n")
def f(a, b):
    if not a: return len(b)
    if not b: return len(a)
    if a[0] == b[0]: return f(a[1:], b[1:])
    return 1 + min(f(a[1:], b), f(a, b[1:]), f(a[1:], b[1:]))
for row in L[1:1 + int(L[0])]:
    a, b = row.split(); print(f(a, b))
""",
        # Compares position by position: wrong as soon as a letter is inserted or dropped.
        "hamming_plus_length_gap": r"""
import sys
L = sys.stdin.read().split("\n")
for row in L[1:1 + int(L[0])]:
    a, b = row.split(); m = min(len(a), len(b))
    print(sum(a[i] != b[i] for i in range(m)) + abs(len(a) - len(b)))
""",
    },
}
