"""«Найди ошибку»: the editor opens with a program that is almost right.

The statement describes the task in full, so a candidate who writes in a language without a
starter solves it from scratch. A starter fails every hidden group: handing it in untouched
earns nothing. Later hidden groups are larger and weigh more.
"""

import random
from dataclasses import replace

from app.seed.code_bank import CodeTask
from app.seed.code_bank.bugfix_starters import STARTERS

EVERYONE = (
    "backend",
    "frontend",
    "fullstack",
    "mobile",
    "gamedev",
    "data-science",
    "data-engineering",
    "devops",
    "qa",
    "security",
)
STARTER_NOTE = (
    "\n\nДля Python, TypeScript, Java, C++, C#, Go и PHP в редакторе уже есть решение с ошибкой: "
    "найдите её и исправьте. На другом языке напишите решение сами."
)
TYPESCRIPT = "typescript-deno"


# ── Lower bound ─────────────────────────────────────────────────────────────────────────────────


def _thresholds(rng: random.Random, size: int, queries: int, top: int) -> str:
    values = sorted(rng.randint(1, top) for _ in range(size))
    asked = [rng.randint(1, top) for _ in range(queries)]
    # Above every element and equal to the last one: the right end of the search.
    asked[rng.randrange(queries)] = values[-1] + 1
    asked[rng.randrange(queries)] = values[-1] + rng.randint(2, 9)
    return f"{size}\n{' '.join(map(str, values))}\n{queries}\n{' '.join(map(str, asked))}\n"


COUNT_BELOW = CodeTask(
    key="count-below",
    title="Сколько порогов пройдено",
    difficulty="medium",
    specializations=EVERYONE,
    topic="debugging",
    statement=(
        "Дан массив из N целых чисел, отсортированный по неубыванию, и Q запросов. Для каждого "
        "запроса x найдите, сколько элементов массива строго меньше x.\n\n"
        "В первой строке — N (1 ≤ N ≤ 5000), во второй — N чисел массива (от 1 до 10^6). В третьей "
        "строке — Q (1 ≤ Q ≤ 3000), в четвёртой — Q чисел x (от 1 до 2·10^6).\n\n"
        "Выведите одно число — сумму ответов на все запросы." + STARTER_NOTE
    ),
    solution="""import sys
from bisect import bisect_left

data = sys.stdin.read().split()
n = int(data[0])
values = [int(item) for item in data[1 : 1 + n]]
q = int(data[1 + n])
print(sum(bisect_left(values, int(item)) for item in data[2 + n : 2 + n + q]))
""",
    brute="""import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(item) for item in data[1 : 1 + n]]
q = int(data[1 + n])
total = 0
for item in data[2 + n : 2 + n + q]:
    total += sum(1 for value in values if value < int(item))
print(total)
""",
    small=lambda rng: _thresholds(rng, rng.randint(1, 8), rng.randint(2, 6), 12),
    sample="5\n2 4 4 7 9\n3\n4 8 1\n",
    hidden=lambda rng: [
        "1\n5\n3\n5 6 1\n",
        _thresholds(rng, 40, 30, 60),
        _thresholds(rng, 5000, 3000, 10**6),
    ],
    weights=(1, 2, 3),
    starter="""import sys


def count_below(values, x):
    lo, hi = 0, len(values) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if values[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


data = sys.stdin.read().split()
n = int(data[0])
values = [int(item) for item in data[1 : 1 + n]]
q = int(data[1 + n])
print(sum(count_below(values, int(item)) for item in data[2 + n : 2 + n + q]))
""",
    starters={
        TYPESCRIPT: """const input = await new Response(Deno.stdin.readable).text()
const data = input.split(/\\s+/).filter(Boolean).map(Number)

function countBelow(values: number[], x: number): number {
  let lo = 0
  let hi = values.length - 1
  while (lo < hi) {
    const mid = (lo + hi) >> 1
    if (values[mid] < x) lo = mid + 1
    else hi = mid
  }
  return lo
}

const n = data[0]
const values = data.slice(1, 1 + n)
const q = data[1 + n]
let total = 0
for (let i = 0; i < q; i++) total += countBelow(values, data[2 + n + i])
console.log(total)
"""
    },
)


# ── Suppressed repeats ──────────────────────────────────────────────────────────────────────────


def _alerts(rng: random.Random, count: int, keys: int, window: int, step: int) -> str:
    # A chain every window must survive: sent, suppressed just before the window ends, sent
    # again right after it. A suppressed alert that extends the window breaks the third one.
    rows = ["0 chain", f"{window - 1} chain", f"{window} chain"]
    now = window
    for _ in range(count - 3):
        now += rng.randint(0, step)
        rows.append(f"{now} k{rng.randint(1, keys)}")
    return f"{count} {window}\n" + "\n".join(rows) + "\n"


ALERT_REPEATS = CodeTask(
    key="alert-repeats",
    title="Подавление повторных оповещений",
    difficulty="medium",
    specializations=EVERYONE,
    topic="debugging",
    statement=(
        "Система оповещений подавляет повторы. Оповещение с ключом k, пришедшее в момент t, "
        "отправляется, если оповещений с этим ключом ещё не отправляли или последнее отправленное "
        "было в момент p и t − p ≥ W. Иначе оно подавляется. Подавленное оповещение окно не "
        "продлевает: считается только время последнего отправленного.\n\n"
        "В первой строке — число оповещений N (1 ≤ N ≤ 4000) и длина окна W (1 ≤ W ≤ 10^9). Далее N "
        "строк в порядке неубывания времени: момент t (0 ≤ t ≤ 10^9) и ключ (латинские буквы и "
        "цифры, до 8 символов).\n\n"
        "Выведите число отправленных оповещений." + STARTER_NOTE
    ),
    solution="""import sys

data = sys.stdin.read().split()
n, window = int(data[0]), int(data[1])
last = {}
sent = 0
for i in range(n):
    now, key = int(data[2 + 2 * i]), data[3 + 2 * i]
    if key not in last or now - last[key] >= window:
        last[key] = now
        sent += 1
print(sent)
""",
    brute="""import sys

data = sys.stdin.read().split()
n, window = int(data[0]), int(data[1])
sent = []
for i in range(n):
    now, key = int(data[2 + 2 * i]), data[3 + 2 * i]
    moments = [moment for moment, who in sent if who == key]
    if not moments or now - max(moments) >= window:
        sent.append((now, key))
print(len(sent))
""",
    small=lambda rng: _alerts(rng, rng.randint(3, 14), 2, rng.randint(2, 6), 3),
    sample="5 10\n0 disk\n4 disk\n9 cpu\n10 disk\n12 cpu\n",
    hidden=lambda rng: [
        _alerts(rng, 12, 2, 5, 2),
        _alerts(rng, 300, 6, 40, 9),
        _alerts(rng, 4000, 50, 1000, 30),
    ],
    weights=(1, 2, 3),
    starter="""import sys

data = sys.stdin.read().split()
n, window = int(data[0]), int(data[1])
last = {}
sent = 0
for i in range(n):
    now, key = int(data[2 + 2 * i]), data[3 + 2 * i]
    if key not in last or now - last[key] >= window:
        sent += 1
    last[key] = now
print(sent)
""",
    starters={
        TYPESCRIPT: """const input = await new Response(Deno.stdin.readable).text()
const data = input.split(/\\s+/).filter(Boolean)

const n = Number(data[0])
const window = Number(data[1])
const last = new Map<string, number>()
let sent = 0
for (let i = 0; i < n; i++) {
  const now = Number(data[2 + 2 * i])
  const key = data[3 + 2 * i]
  const previous = last.get(key)
  if (previous === undefined || now - previous >= window) sent += 1
  last.set(key, now)
}
console.log(sent)
"""
    },
)


# ── Weighted shortest path ──────────────────────────────────────────────────────────────────────


def _graph(rng: random.Random, nodes: int, edges: int, shortcut: bool) -> str:
    """Random heavy edges; with `shortcut`, a cheap detour 1 → 3 → 2 → n next to a dearer direct
    edge 1 → 2: the vertex 2 is reached first by the worse way."""
    rows = []
    if shortcut:
        first, second, last = (rng.randint(1, 60) for _ in range(3))
        rows += [
            f"1 2 {first + second + rng.randint(1, 60)}",
            f"1 3 {first}",
            f"3 2 {second}",
            f"2 {nodes} {last}",
        ]
    for _ in range(edges - len(rows)):
        rows.append(f"{rng.randint(1, nodes)} {rng.randint(1, nodes)} {rng.randint(1000, 10**5)}")
    rng.shuffle(rows)
    return f"{nodes} {len(rows)}\n" + "\n".join(rows)


def _routes(rng: random.Random, sizes: list[tuple[int, int, bool]]) -> str:
    return f"{len(sizes)}\n" + "\n".join(_graph(rng, *size) for size in sizes) + "\n"


CHEAPEST_ROUTE = CodeTask(
    key="cheapest-route",
    title="Самый дешёвый маршрут",
    difficulty="hard",
    specializations=EVERYONE,
    topic="debugging",
    statement=(
        "Дан ориентированный граф: вершины пронумерованы от 1 до N, у каждого ребра есть "
        "стоимость. Найдите наименьшую суммарную стоимость пути из вершины 1 в вершину N.\n\n"
        "В первой строке — число наборов T (1 ≤ T ≤ 40). Каждый набор начинается строкой с числом "
        "вершин N (4 ≤ N ≤ 1000) и числом рёбер M (1 ≤ M ≤ 3000); далее M строк: начало ребра, "
        "конец ребра и стоимость (от 1 до 10^5). Сумма M по всем наборам не превышает 3000.\n\n"
        "Для каждого набора выведите в отдельной строке наименьшую стоимость или -1, если пути "
        "нет." + STARTER_NOTE
    ),
    solution="""import heapq
import sys

data = sys.stdin.read().split()
pos = 1
answers = []
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    pos += 2
    graph = [[] for _ in range(n + 1)]
    for _ in range(m):
        graph[int(data[pos])].append((int(data[pos + 1]), int(data[pos + 2])))
        pos += 3
    best = [None] * (n + 1)
    best[1] = 0
    heap = [(0, 1)]
    while heap:
        cost, node = heapq.heappop(heap)
        if cost > best[node]:
            continue
        for target, price in graph[node]:
            total = cost + price
            if best[target] is None or total < best[target]:
                best[target] = total
                heapq.heappush(heap, (total, target))
    answers.append(-1 if best[n] is None else best[n])
print("\\n".join(map(str, answers)))
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    pos += 2
    edges = []
    for _ in range(m):
        edges.append((int(data[pos]), int(data[pos + 1]), int(data[pos + 2])))
        pos += 3
    best = {1: 0}
    for _ in range(n):
        for start, target, price in edges:
            if start in best and best[start] + price < best.get(target, 10**18):
                best[target] = best[start] + price
    print(best.get(n, -1))
""",
    small=lambda rng: _routes(
        rng, [(rng.randint(4, 7), rng.randint(4, 12), rng.random() < 0.5) for _ in range(4)]
    ),
    sample="2\n4 4\n1 2 5\n1 3 1\n3 2 1\n2 4 1\n4 2\n2 3 7\n3 4 2\n",
    hidden=lambda rng: [
        _routes(rng, [(5, 6, True), (6, 5, False), (8, 14, True)]),
        _routes(rng, [(40, 120, True), (30, 60, False), (60, 200, True), (25, 80, True)]),
        _routes(rng, [(1000, 1800, True), (400, 600, False), (300, 600, True)]),
    ],
    weights=(1, 2, 3),
    starter="""import heapq
import sys

data = sys.stdin.read().split()
pos = 1
answers = []
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    pos += 2
    graph = [[] for _ in range(n + 1)]
    for _ in range(m):
        graph[int(data[pos])].append((int(data[pos + 1]), int(data[pos + 2])))
        pos += 3
    best = [None] * (n + 1)
    best[1] = 0
    heap = [(0, 1)]
    while heap:
        cost, node = heapq.heappop(heap)
        for target, price in graph[node]:
            if best[target] is None:
                best[target] = cost + price
                heapq.heappush(heap, (best[target], target))
    answers.append(-1 if best[n] is None else best[n])
print("\\n".join(map(str, answers)))
""",
    starters={
        TYPESCRIPT: """const input = await new Response(Deno.stdin.readable).text()
const data = input.split(/\\s+/).filter(Boolean).map(Number)

// Двоичная куча пар [стоимость, вершина] с минимумом на вершине.
const heap: [number, number][] = []

function push(item: [number, number]): void {
  heap.push(item)
  let i = heap.length - 1
  while (i > 0) {
    const parent = (i - 1) >> 1
    if (heap[parent][0] <= heap[i][0]) break
    ;[heap[parent], heap[i]] = [heap[i], heap[parent]]
    i = parent
  }
}

function pop(): [number, number] {
  const top = heap[0]
  const tail = heap.pop()!
  if (heap.length > 0) {
    heap[0] = tail
    let i = 0
    while (true) {
      let least = i
      for (const child of [2 * i + 1, 2 * i + 2]) {
        if (child < heap.length && heap[child][0] < heap[least][0]) least = child
      }
      if (least === i) break
      ;[heap[least], heap[i]] = [heap[i], heap[least]]
      i = least
    }
  }
  return top
}

let pos = 1
const answers: number[] = []
for (let test = 0; test < data[0]; test++) {
  const n = data[pos]
  const m = data[pos + 1]
  pos += 2
  const graph: [number, number][][] = Array.from({ length: n + 1 }, () => [])
  for (let i = 0; i < m; i++) {
    graph[data[pos]].push([data[pos + 1], data[pos + 2]])
    pos += 3
  }
  const best = new Array<number>(n + 1).fill(-1)
  best[1] = 0
  push([0, 1])
  while (heap.length > 0) {
    const [cost, node] = pop()
    for (const [target, price] of graph[node]) {
      if (best[target] === -1) {
        best[target] = cost + price
        push([best[target], target])
      }
    }
  }
  answers.push(best[n])
}
console.log(answers.join('\\n'))
"""
    },
)


# ── 0/1 knapsack ────────────────────────────────────────────────────────────────────────────────


def _crates(rng: random.Random, count: int, capacity: int, heavy: int, worth: int) -> str:
    rows = [f"{rng.randint(1, heavy)} {rng.randint(1, worth)}" for _ in range(count)]
    return f"{count} {capacity}\n" + "\n".join(rows) + "\n"


CARGO = CodeTask(
    key="cargo-value",
    title="Загрузка контейнера",
    difficulty="hard",
    specializations=EVERYONE,
    topic="debugging",
    statement=(
        "В контейнер грузоподъёмностью C нужно положить ящики так, чтобы их суммарная ценность "
        "была наибольшей. Каждый ящик существует в одном экземпляре: его можно взять целиком или "
        "не брать вовсе.\n\n"
        "В первой строке — число ящиков N (1 ≤ N ≤ 200) и грузоподъёмность C (1 ≤ C ≤ 5000). Далее N "
        "строк: вес ящика (от 1 до 5000) и его ценность (от 1 до 10^6).\n\n"
        "Выведите наибольшую суммарную ценность ящиков, общий вес которых не превышает C."
        + STARTER_NOTE
    ),
    solution="""import sys

data = sys.stdin.read().split()
n, capacity = int(data[0]), int(data[1])
best = [0] * (capacity + 1)
for i in range(n):
    weight, value = int(data[2 + 2 * i]), int(data[3 + 2 * i])
    for load in range(capacity, weight - 1, -1):
        candidate = best[load - weight] + value
        if candidate > best[load]:
            best[load] = candidate
print(best[capacity])
""",
    brute="""import sys

data = sys.stdin.read().split()
n, capacity = int(data[0]), int(data[1])
crates = [(int(data[2 + 2 * i]), int(data[3 + 2 * i])) for i in range(n)]
best = 0
for mask in range(1 << n):
    weight = sum(crates[i][0] for i in range(n) if mask >> i & 1)
    if weight <= capacity:
        best = max(best, sum(crates[i][1] for i in range(n) if mask >> i & 1))
print(best)
""",
    small=lambda rng: _crates(rng, rng.randint(1, 9), rng.randint(1, 20), 8, 30),
    sample="3 10\n4 30\n5 20\n7 45\n",
    hidden=lambda rng: [
        "2 9\n3 10\n5 4\n",
        _crates(rng, 30, 200, 40, 500),
        _crates(rng, 200, 5000, 400, 10**6),
    ],
    weights=(1, 2, 3),
    starter="""import sys

data = sys.stdin.read().split()
n, capacity = int(data[0]), int(data[1])
best = [0] * (capacity + 1)
for i in range(n):
    weight, value = int(data[2 + 2 * i]), int(data[3 + 2 * i])
    for load in range(weight, capacity + 1):
        candidate = best[load - weight] + value
        if candidate > best[load]:
            best[load] = candidate
print(best[capacity])
""",
    starters={
        TYPESCRIPT: """const input = await new Response(Deno.stdin.readable).text()
const data = input.split(/\\s+/).filter(Boolean).map(Number)

const n = data[0]
const capacity = data[1]
const best = new Array<number>(capacity + 1).fill(0)
for (let i = 0; i < n; i++) {
  const weight = data[2 + 2 * i]
  const value = data[3 + 2 * i]
  for (let load = weight; load <= capacity; load++) {
    best[load] = Math.max(best[load], best[load - weight] + value)
  }
}
console.log(best[capacity])
"""
    },
)


TASKS = [
    replace(task, starters={**(task.starters or {}), **STARTERS[task.key]})
    for task in (COUNT_BELOW, ALERT_REPEATS, CHEAPEST_ROUTE, CARGO)
]
