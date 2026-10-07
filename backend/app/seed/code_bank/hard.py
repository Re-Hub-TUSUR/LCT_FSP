"""Hard tasks: dynamic programming, weighted graphs, a search over the answer."""

import random

from app.seed.code_bank import CodeTask


def _lines(cases: int, rows: list[str]) -> str:
    return f"{cases}\n" + "\n".join(rows) + "\n"


def _batches(rng: random.Random, cases: int, size: int, top: int, full: bool = False) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        rows.append(f"{n} {rng.randint(1, n)}")
        rows.append(" ".join(str(rng.randint(1, top)) for _ in range(n)))
    return _lines(cases, rows)


SPLIT_BATCHES = CodeTask(
    key="split-batches",
    title="Разбиение очереди на пакеты",
    difficulty="hard",
    specializations=("devops", "backend", "data-engineering"),
    topic="algorithms",
    statement=(
        "В очереди n заданий, у каждого известен объём. Очередь нужно разрезать на k пакетов: "
        "каждый пакет — непустой отрезок идущих подряд заданий, порядок заданий менять нельзя. "
        "Нагрузка пакета — сумма объёмов его заданий. Требуется сделать наибольшую нагрузку пакета "
        "как можно меньше.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест занимает две строки: числа n и k "
        "(1 ≤ k ≤ n ≤ 3000) и n объёмов — целые числа от 1 до 10^9. Для каждого теста выведите "
        "наименьшее возможное значение наибольшей нагрузки."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, k = int(data[pos]), int(data[pos + 1])
    sizes = [int(item) for item in data[pos + 2 : pos + 2 + n]]
    pos += 2 + n
    low, high = max(sizes), sum(sizes)
    while low < high:
        middle = (low + high) // 2
        packs, load = 1, 0
        for size in sizes:
            if load + size > middle:
                packs += 1
                load = size
            else:
                load += size
        if packs <= k:
            high = middle
        else:
            low = middle + 1
    print(low)
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, k = int(data[pos]), int(data[pos + 1])
    sizes = [int(item) for item in data[pos + 2 : pos + 2 + n]]
    pos += 2 + n
    best = [[None] * (n + 1) for _ in range(k + 1)]
    best[0][0] = 0
    for packs in range(1, k + 1):
        for end in range(packs, n + 1):
            options = [
                max(best[packs - 1][cut], sum(sizes[cut:end]))
                for cut in range(packs - 1, end)
                if best[packs - 1][cut] is not None
            ]
            best[packs][end] = min(options)
    print(best[k][n])
""",
    small=lambda rng: _batches(rng, 15, 8, 9),
    sample="3\n5 2\n4 2 7 1 3\n4 4\n5 1 8 2\n3 1\n10 20 30\n",
    hidden=lambda rng: [
        "3\n1 1\n7\n6 3\n1 1 1 1 1 1\n5 2\n1000000000 1000000000 1000000000 1000000000 1000000000\n",
        _batches(rng, 30, 10, 12),
        _batches(rng, 20, 250, 1000),
        _batches(rng, 1, 3000, 10**9, full=True),
        _batches(rng, 3, 3000, 3, full=True),
    ],
)


def _plan(
    rng: random.Random,
    cases: int,
    size: int,
    edges: int,
    top: int,
    cyclic: float,
    full: bool = False,
) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        order = list(range(1, n + 1))
        rng.shuffle(order)
        pairs = []
        if n > 1:
            chain = rng.randint(0, n - 1)
            pairs += [(order[i + 1], order[i]) for i in range(chain) if rng.random() < 0.8]
            for _ in range(rng.randint(0, max(0, min(edges, 3 * n) - chain))):
                low, high = sorted(rng.sample(range(n), 2))
                pairs.append((order[high], order[low]))
        if rng.random() < cyclic:
            pairs.append((rng.randint(1, n), rng.randint(1, n)))
        rng.shuffle(pairs)
        rows.append(f"{n} {len(pairs)}")
        rows.append(" ".join(str(rng.randint(1, top)) for _ in range(n)))
        rows += [f"{a} {b}" for a, b in pairs]
    return _lines(cases, rows)


CRITICAL_PATH = CodeTask(
    key="critical-path",
    title="Длительность конвейера",
    difficulty="hard",
    specializations=("devops", "data-engineering", "backend", "qa"),
    topic="graphs",
    statement=(
        "Конвейер состоит из n задач с номерами от 1 до n, для каждой известна длительность. "
        "Задача может начаться только после завершения всех задач, от которых она зависит. "
        "Исполнителей сколько угодно: любое число задач может выполняться одновременно.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест начинается строкой с числами n и m "
        "(1 ≤ n ≤ 1500, 0 ≤ m ≤ 3000), затем строка с n длительностями — целыми числами от 1 до "
        "10^9, затем m строк «a b»: задача a зависит от задачи b. Зависимости могут повторяться, "
        "задача может зависеть сама от себя.\n\n"
        "Для каждого теста выведите наименьшее время, за которое завершится весь конвейер, или "
        "CYCLE, если из-за циклической зависимости он не завершится никогда."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    duration = [0] + [int(item) for item in data[pos + 2 : pos + 2 + n]]
    pos += 2 + n
    children = [[] for _ in range(n + 1)]
    waiting = [0] * (n + 1)
    for _ in range(m):
        a, b = int(data[pos]), int(data[pos + 1])
        pos += 2
        children[b].append(a)
        waiting[a] += 1
    start = [0] * (n + 1)
    ready = [task for task in range(1, n + 1) if waiting[task] == 0]
    done = total = 0
    while ready:
        task = ready.pop()
        done += 1
        finish = start[task] + duration[task]
        total = max(total, finish)
        for child in children[task]:
            start[child] = max(start[child], finish)
            waiting[child] -= 1
            if waiting[child] == 0:
                ready.append(child)
    print(total if done == n else "CYCLE")
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    duration = [0] + [int(item) for item in data[pos + 2 : pos + 2 + n]]
    pos += 2 + n
    needs = {task: set() for task in range(1, n + 1)}
    for _ in range(m):
        needs[int(data[pos])].add(int(data[pos + 1]))
        pos += 2
    finish = {}
    while len(finish) < n:
        ready = [task for task in needs if task not in finish and needs[task] <= finish.keys()]
        if not ready:
            break
        for task in ready:
            finish[task] = duration[task] + max((finish[item] for item in needs[task]), default=0)
    print(max(finish.values()) if len(finish) == n else "CYCLE")
""",
    small=lambda rng: _plan(rng, 15, 7, 12, 9, 0.3),
    sample="3\n4 3\n3 2 4 1\n2 1\n3 1\n4 3\n2 2\n5 5\n1 2\n2 1\n3 0\n7 2 9\n",
    hidden=lambda rng: [
        "3\n1 0\n5\n1 1\n5\n1 1\n3 3\n1000000000 1000000000 1000000000\n2 1\n3 2\n3 1\n",
        _plan(rng, 30, 8, 14, 20, 0.3),
        _plan(rng, 20, 120, 200, 1000, 0.15),
        _plan(rng, 1, 1500, 2998, 10**9, 0.0, full=True),
        _plan(rng, 1, 1500, 2998, 100, 0.0, full=True),
    ],
)


def _feed(
    rng: random.Random, cases: int, size: int, kinds: int, noise: int, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        k = rng.randint(1, min(kinds, n))
        feed = [rng.randint(1, k + rng.randint(0, noise)) for _ in range(n)]
        span = k + rng.randint(0, k)
        if span <= n and (full or rng.random() < 0.7):
            # Random events alone rarely cover many kinds: plant every kind into one stretch.
            start = rng.randint(0, n - span)
            for kind, spot in enumerate(rng.sample(range(start, start + span), k), start=1):
                feed[spot] = kind
        rows.append(f"{n} {k}")
        rows.append(" ".join(map(str, feed)))
    return _lines(cases, rows)


MIN_WINDOW = CodeTask(
    key="min-window",
    title="Кратчайший полный фрагмент журнала",
    difficulty="hard",
    specializations=("security", "devops", "data-engineering"),
    topic="logs",
    statement=(
        "Журнал аудита — последовательность из n событий, у каждого есть тип — целое число. Для "
        "расследования нужен фрагмент журнала из идущих подряд событий, в котором хотя бы по одному "
        "разу встречается каждый из типов 1, 2, …, k. События других типов во фрагменте допустимы.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест занимает две строки: числа n и k "
        "(1 ≤ k ≤ n ≤ 5000) и n типов событий — целые числа от 1 до 10^9. Для каждого теста выведите "
        "длину кратчайшего подходящего фрагмента или 0, если такого фрагмента нет."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, k = int(data[pos]), int(data[pos + 1])
    kinds = [int(item) for item in data[pos + 2 : pos + 2 + n]]
    pos += 2 + n
    inside = [0] * (k + 1)
    missing = k
    best = left = 0
    for right, kind in enumerate(kinds):
        if kind <= k:
            if inside[kind] == 0:
                missing -= 1
            inside[kind] += 1
        while missing == 0:
            if best == 0 or right - left + 1 < best:
                best = right - left + 1
            gone = kinds[left]
            left += 1
            if gone <= k:
                inside[gone] -= 1
                if inside[gone] == 0:
                    missing += 1
    print(best)
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, k = int(data[pos]), int(data[pos + 1])
    kinds = [int(item) for item in data[pos + 2 : pos + 2 + n]]
    pos += 2 + n
    need = set(range(1, k + 1))
    best = 0
    for left in range(n):
        for right in range(left, n):
            if need <= set(kinds[left : right + 1]):
                if best == 0 or right - left + 1 < best:
                    best = right - left + 1
                break
    print(best)
""",
    small=lambda rng: _feed(rng, 15, 10, 4, 2),
    sample="3\n8 3\n1 5 2 2 3 1 4 2\n4 2\n1 1 3 1\n3 3\n3 2 1\n",
    hidden=lambda rng: [
        "4\n1 1\n1\n1 1\n2\n5 1\n7 1000000000 1 7 7\n6 3\n1 2 1 2 3 3\n",
        _feed(rng, 30, 12, 4, 2),
        _feed(rng, 20, 300, 12, 6),
        _feed(rng, 3, 5000, 40, 20, full=True),
        _feed(rng, 2, 5000, 2500, 5, full=True),
    ],
)


def _firewall(rng: random.Random, rules: int, ports: int, width: int) -> str:
    rows = [f"{rules} {ports}"]
    for _ in range(rules):
        low = rng.randint(1, ports)
        high = min(ports, low + rng.randint(0, width))
        rows.append(f"{rng.choice(('allow', 'deny'))} {low} {high}")
    return "\n".join(rows) + "\n"


FIREWALL_RULES = CodeTask(
    key="firewall-rules",
    title="Открытые порты",
    difficulty="hard",
    specializations=("security", "devops"),
    topic="algorithms",
    statement=(
        "Межсетевой экран хранит упорядоченный список правил. Каждое правило — действие allow или "
        "deny и отрезок номеров портов. Для порта срабатывает первое по порядку правило, отрезок "
        "которого его содержит; если ни одно правило не подошло, порт закрыт.\n\n"
        "В первой строке — число правил R (1 ≤ R ≤ 700) и наибольший номер порта P (1 ≤ P ≤ 10^12). "
        "В каждой из следующих R строк — действие и два целых числа lo и hi (1 ≤ lo ≤ hi ≤ P): "
        "правило относится к портам от lo до hi включительно.\n\n"
        "Выведите, сколько портов с номерами от 1 до P открыто."
    ),
    solution="""import sys

data = sys.stdin.read().split()
count = int(data[0])
rules = [
    (data[2 + 3 * i] == "allow", int(data[3 + 3 * i]), int(data[4 + 3 * i])) for i in range(count)
]
edges = sorted({low for _, low, _ in rules} | {high + 1 for _, _, high in rules})
opened = 0
for start, end in zip(edges, edges[1:]):
    for allow, low, high in rules:
        if low <= start <= high:
            if allow:
                opened += end - start
            break
print(opened)
""",
    brute="""import sys

data = sys.stdin.read().split()
count, ports = int(data[0]), int(data[1])
rules = [
    (data[2 + 3 * i] == "allow", int(data[3 + 3 * i]), int(data[4 + 3 * i])) for i in range(count)
]
opened = 0
for port in range(1, ports + 1):
    for allow, low, high in rules:
        if low <= port <= high:
            opened += allow
            break
print(opened)
""",
    small=lambda rng: _firewall(rng, rng.randint(1, 7), rng.randint(1, 30), 12),
    sample="4 100\ndeny 20 29\nallow 10 50\ndeny 1 100\nallow 90 95\n",
    hidden=lambda rng: [
        "3 10\nallow 1 10\ndeny 1 10\nallow 5 5\n",
        _firewall(rng, 12, 60, 20),
        _firewall(rng, 300, 10**6, 10**4),
        _firewall(rng, 700, 10**12, 10**11),
        _firewall(rng, 700, 10**12, 10**6),
    ],
)


def _dag(rng: random.Random, cases: int, size: int, edges: int, full: bool = False) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        order = list(range(1, n + 1))
        rng.shuffle(order)
        pairs = set()
        if n > 1 and (full or rng.random() < 0.75):
            # Source first, target last and a backbone between them, so paths are plentiful.
            order.remove(1)
            order.remove(n)
            order = [1, *order, n]
            keep = rng.choice((1.0, 0.97))
            pairs |= {(order[i], order[i + 1]) for i in range(n - 1) if rng.random() < keep}
        if n > 1:
            for _ in range(
                edges - len(pairs) if full else rng.randint(0, max(0, edges - len(pairs)))
            ):
                low = rng.randrange(n - 1)
                jump = rng.randint(1, 4) if rng.random() < 0.7 else rng.randint(1, n)
                pairs.add((order[low], order[min(n - 1, low + jump)]))
        listed = sorted(pairs)
        rng.shuffle(listed)
        rows.append(f"{n} {len(listed)}")
        rows += [f"{a} {b}" for a, b in listed]
    return _lines(cases, rows)


ACCESS_PATHS = CodeTask(
    key="access-paths",
    title="Пути повышения привилегий",
    difficulty="hard",
    specializations=("security", "backend"),
    topic="dynamic-programming",
    statement=(
        "Модель угроз — ориентированный граф без циклов: вершины с номерами от 1 до n — уровни "
        "доступа, ребро «a b» означает, что с уровня a можно за один шаг получить уровень b. "
        "Атакующий начинает на уровне 1, его цель — уровень n. Путь атаки — последовательность "
        "шагов по рёбрам от вершины 1 до вершины n.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест начинается строкой с числами n и m "
        "(1 ≤ n ≤ 2000, 0 ≤ m ≤ 4000), далее m строк с рёбрами. Гарантируется, что в графе нет "
        "циклов и повторяющихся рёбер; номера вершин не обязаны возрастать вдоль рёбер.\n\n"
        "Для каждого теста выведите число различных путей атаки по модулю 1 000 000 007. При n = 1 "
        "ответ равен 1."
    ),
    solution="""import sys

MOD = 10**9 + 7
data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    pos += 2
    following = [[] for _ in range(n + 1)]
    incoming = [0] * (n + 1)
    for _ in range(m):
        a, b = int(data[pos]), int(data[pos + 1])
        pos += 2
        following[a].append(b)
        incoming[b] += 1
    ways = [0] * (n + 1)
    ways[1] = 1
    ready = [vertex for vertex in range(1, n + 1) if incoming[vertex] == 0]
    while ready:
        vertex = ready.pop()
        for target in following[vertex]:
            ways[target] = (ways[target] + ways[vertex]) % MOD
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    print(ways[n])
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    pos += 2
    following = {vertex: [] for vertex in range(1, n + 1)}
    for _ in range(m):
        following[int(data[pos])].append(int(data[pos + 1]))
        pos += 2

    def count(vertex):
        if vertex == n:
            return 1
        return sum(count(target) for target in following[vertex])

    print(count(1) % (10**9 + 7))
""",
    small=lambda rng: _dag(rng, 15, 8, 16),
    sample="3\n4 5\n1 2\n1 3\n2 4\n3 4\n2 3\n3 1\n3 1\n1 0\n",
    hidden=lambda rng: [
        "3\n1 0\n2 0\n2 1\n1 2\n",
        _dag(rng, 30, 9, 20),
        _dag(rng, 20, 150, 400),
        _dag(rng, 1, 2000, 4000, full=True),
        _dag(rng, 1, 2000, 4000, full=True),
    ],
)


def _split(
    rng: random.Random, cases: int, words: int, length: int, alphabet: str, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        k = rng.randint(1, words)
        tokens = sorted(
            {"".join(rng.choice(alphabet) for _ in range(rng.randint(1, 4))) for _ in range(k)}
        )
        rng.shuffle(tokens)
        text = ""
        while len(text) < (length if full else rng.randint(1, length)):
            text += rng.choice(tokens)
        if not full and rng.random() < 0.25:
            spot = rng.randrange(len(text))
            text = text[:spot] + rng.choice(alphabet) + text[spot + 1 :]
        rows.append(str(len(tokens)))
        rows.append(" ".join(tokens))
        rows.append(text[:length])
    return _lines(cases, rows)


TOKEN_SPLIT = CodeTask(
    key="token-split",
    title="Разбор строки по словарю",
    difficulty="hard",
    specializations=("security", "qa", "backend"),
    topic="dynamic-programming",
    statement=(
        "Фильтр ввода знает словарь из k различных лексем — строк из строчных латинских букв. "
        "Разбором строки s называется способ представить её как последовательность лексем словаря, "
        "записанных подряд без разделителей; одну лексему можно использовать сколько угодно раз. "
        "Два разбора различны, если различаются последовательности лексем.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест занимает три строки: число k "
        "(1 ≤ k ≤ 50), k лексем через пробел (длина каждой от 1 до 20) и строка s длиной от 1 до "
        "2000. Для каждого теста выведите число разборов строки s по модулю 1 000 000 007."
    ),
    solution="""import sys

MOD = 10**9 + 7
data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    k = int(data[pos])
    tokens = set(data[pos + 1 : pos + 1 + k])
    text = data[pos + 1 + k]
    pos += 2 + k
    lengths = sorted({len(token) for token in tokens})
    ways = [0] * (len(text) + 1)
    ways[0] = 1
    for end in range(1, len(text) + 1):
        total = 0
        for length in lengths:
            if length > end:
                break
            if ways[end - length] and text[end - length : end] in tokens:
                total += ways[end - length]
        ways[end] = total % MOD
    print(ways[len(text)])
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    k = int(data[pos])
    tokens = data[pos + 1 : pos + 1 + k]
    text = data[pos + 1 + k]
    pos += 2 + k

    def count(rest):
        if not rest:
            return 1
        return sum(count(rest[len(token) :]) for token in tokens if rest.startswith(token))

    print(count(text) % (10**9 + 7))
""",
    small=lambda rng: _split(rng, 15, 5, 12, "ab"),
    sample="3\n3\na ab b\nabab\n2\ncat dog\ncatdogcat\n2\nx yy\nxyx\n",
    hidden=lambda rng: [
        "3\n1\na\na\n1\nab\na\n3\na aa aaa\naaaaaaaaaa\n",
        _split(rng, 30, 6, 14, "ab"),
        _split(rng, 30, 20, 300, "abc"),
        _split(rng, 10, 50, 2000, "ab", full=True),
        _split(rng, 10, 50, 2000, "abcdef", full=True),
    ],
)


def _texts(rng: random.Random, cases: int, size: int, spread: int, full: bool = False) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        first = [rng.randint(1, spread) for _ in range(n)]
        second = [item for item in first if rng.random() < 0.8]
        for _ in range(rng.randint(0, max(1, n // 4))):
            second.insert(rng.randint(0, len(second)), rng.randint(1, spread))
        second = second[:size] or [rng.randint(1, spread)]
        rows.append(f"{n} {len(second)}")
        rows.append(" ".join(map(str, first)))
        rows.append(" ".join(map(str, second)))
    return _lines(cases, rows)


LCS_DIFF = CodeTask(
    key="lcs-diff",
    title="Размер диффа",
    difficulty="hard",
    specializations=("qa", "frontend", "fullstack"),
    topic="dynamic-programming",
    statement=(
        "Две версии файла сравнивают построчно; каждая строка заменена своим идентификатором — "
        "целым числом, равные строки имеют равные идентификаторы. Дифф состоит из удалений строк "
        "первой версии и вставок строк второй версии: после удалений и вставок первая версия должна "
        "превратиться во вторую. Замены строки нет — это удаление и вставка.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест занимает три строки: числа строк n и m "
        "в версиях (1 ≤ n, m ≤ 1000), n идентификаторов первой версии и m идентификаторов второй — "
        "целые числа от 1 до 10^9. Сумма произведений n·m по всем тестам одного входа не превышает "
        "10^6.\n\n"
        "Для каждого теста выведите наименьшее возможное суммарное число удалений и вставок."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    first = data[pos + 2 : pos + 2 + n]
    second = data[pos + 2 + n : pos + 2 + n + m]
    pos += 2 + n + m
    previous = [0] * (m + 1)
    for line in first:
        current = [0] * (m + 1)
        best = 0
        for j in range(m):
            if second[j] == line:
                best = previous[j] + 1
            elif previous[j + 1] > best:
                best = previous[j + 1]
            current[j + 1] = best
        previous = current
    print(n + m - 2 * previous[m])
""",
    brute="""import sys
from itertools import combinations

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    first = data[pos + 2 : pos + 2 + n]
    second = data[pos + 2 + n : pos + 2 + n + m]
    pos += 2 + n + m
    common = 0
    for size in range(1, min(n, m) + 1):
        kept = {tuple(first[i] for i in picked) for picked in combinations(range(n), size)}
        if any(tuple(second[j] for j in picked) in kept for picked in combinations(range(m), size)):
            common = size
    print(n + m - 2 * common)
""",
    small=lambda rng: _texts(rng, 12, 7, 3),
    sample="3\n4 4\n1 2 3 4\n1 3 4 5\n2 3\n7 7\n7 7 7\n3 2\n1 2 3\n4 5\n",
    hidden=lambda rng: [
        "3\n1 1\n5\n5\n1 1\n5\n6\n5 5\n1 2 3 4 5\n5 4 3 2 1\n",
        _texts(rng, 30, 8, 3),
        _texts(rng, 25, 190, 12),
        _texts(rng, 1, 1000, 30, full=True),
        _texts(rng, 1, 1000, 10**9, full=True),
    ],
)


def _suites(
    rng: random.Random, cases: int, needs: int, tests: int, width: int, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        r, n = (needs, tests) if full else (rng.randint(1, needs), rng.randint(1, tests))
        rows.append(f"{r} {n}")
        for _ in range(n):
            covered = sorted(rng.sample(range(1, r + 1), rng.randint(1, min(r, width))))
            rows.append(f"{len(covered)} " + " ".join(map(str, covered)))
    return _lines(cases, rows)


MIN_TEST_SET = CodeTask(
    key="min-test-set",
    title="Минимальный набор тестов",
    difficulty="hard",
    specializations=("qa",),
    topic="dynamic-programming",
    statement=(
        "В проекте r требований с номерами от 1 до r и n автотестов; про каждый тест известно, "
        "какие требования он проверяет. Для смоук-прогона нужно выбрать как можно меньше тестов "
        "так, чтобы каждое требование проверялось хотя бы одним выбранным тестом.\n\n"
        "В первой строке — число наборов входных данных T (1 ≤ T ≤ 30). Набор начинается строкой с "
        "числами r и n (1 ≤ r ≤ 14, 1 ≤ n ≤ 30), далее n строк: число c проверяемых тестом "
        "требований (1 ≤ c ≤ r) и c различных номеров требований. Сумма значений n·2^r по всем "
        "наборам одного входа не превышает 10^6.\n\n"
        "Для каждого набора выведите наименьшее число тестов, покрывающих все требования, или −1, "
        "если покрыть все требования невозможно."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    r, n = int(data[pos]), int(data[pos + 1])
    pos += 2
    masks = set()
    for _ in range(n):
        c = int(data[pos])
        mask = 0
        for item in data[pos + 1 : pos + 1 + c]:
            mask |= 1 << (int(item) - 1)
        masks.add(mask)
        pos += 1 + c
    full = (1 << r) - 1
    limit = n + 1
    best = [limit] * (full + 1)
    best[0] = 0
    for state in range(full):
        used = best[state] + 1
        if used > limit:
            continue
        for mask in masks:
            merged = state | mask
            if best[merged] > used:
                best[merged] = used
    print(best[full] if best[full] < limit else -1)
""",
    brute="""import sys
from itertools import combinations

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    r, n = int(data[pos]), int(data[pos + 1])
    pos += 2
    tests = []
    for _ in range(n):
        c = int(data[pos])
        tests.append({int(item) for item in data[pos + 1 : pos + 1 + c]})
        pos += 1 + c
    need = set(range(1, r + 1))
    answer = -1
    for size in range(1, n + 1):
        if any(need <= set().union(*picked) for picked in combinations(tests, size)):
            answer = size
            break
    print(answer)
""",
    small=lambda rng: _suites(rng, 12, 6, 7, 3),
    sample="3\n4 4\n2 1 2\n2 3 4\n3 1 2 3\n1 4\n3 2\n1 1\n1 2\n2 3\n2 1 2\n1 2\n1 1\n",
    hidden=lambda rng: [
        "3\n1 1\n1 1\n3 3\n1 1\n1 2\n1 3\n3 4\n3 1 2 3\n1 1\n1 2\n1 3\n",
        _suites(rng, 30, 6, 8, 3),
        _suites(rng, 30, 9, 20, 4),
        _suites(rng, 2, 14, 30, 4, full=True),
        _suites(rng, 2, 14, 30, 3, full=True),
    ],
)


def _items(
    rng: random.Random, cases: int, size: int, budget: int, value: int, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        n, limit = (size, budget) if full else (rng.randint(1, size), rng.randint(1, budget))
        rows.append(f"{n} {limit}")
        rows += [
            f"{rng.randint(1, max(1, limit * 2 // 3))} {rng.randint(1, value)}" for _ in range(n)
        ]
    return _lines(cases, rows)


KNAPSACK_BUDGET = CodeTask(
    key="knapsack-budget",
    title="Отбор в пределах бюджета",
    difficulty="hard",
    specializations=("data-science", "backend", "gamedev", "mobile"),
    topic="dynamic-programming",
    statement=(
        "Есть n предметов, у каждого — стоимость и ценность. Нужно выбрать набор предметов с "
        "суммарной стоимостью не больше бюджета W и наибольшей суммарной ценностью; каждый предмет "
        "можно взять не более одного раза.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест начинается строкой с числами n и W "
        "(1 ≤ n ≤ 100, 1 ≤ W ≤ 3000), далее n строк с двумя целыми числами: стоимость (от 1 до "
        "3000) и ценность (от 1 до 10^9). Сумма произведений n·W по всем тестам одного входа не "
        "превышает 2·10^6.\n\n"
        "Для каждого теста выведите наибольшую достижимую суммарную ценность."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, limit = int(data[pos]), int(data[pos + 1])
    pos += 2
    best = [0] * (limit + 1)
    for _ in range(n):
        cost, value = int(data[pos]), int(data[pos + 1])
        pos += 2
        for budget in range(limit, cost - 1, -1):
            candidate = best[budget - cost] + value
            if candidate > best[budget]:
                best[budget] = candidate
    print(best[limit])
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, limit = int(data[pos]), int(data[pos + 1])
    pos += 2
    items = [(int(data[pos + 2 * i]), int(data[pos + 1 + 2 * i])) for i in range(n)]
    pos += 2 * n
    best = 0
    for chosen in range(1 << n):
        picked = [items[i] for i in range(n) if chosen >> i & 1]
        if sum(cost for cost, _ in picked) <= limit:
            best = max(best, sum(value for _, value in picked))
    print(best)
""",
    small=lambda rng: _items(rng, 12, 8, 14, 20),
    sample="2\n4 10\n5 10\n4 40\n6 30\n3 50\n2 3\n4 100\n5 200\n",
    hidden=lambda rng: [
        "3\n1 1\n1 5\n1 1\n2 5\n3 6\n3 4\n3 5\n3 6\n",
        _items(rng, 30, 9, 16, 30),
        _items(rng, 30, 40, 300, 1000),
        _items(rng, 6, 100, 3000, 10**9, full=True),
        _items(rng, 6, 100, 3000, 5, full=True),
    ],
)


def _points(
    rng: random.Random, cases: int, size: int, top: int, groups: int, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        rows.append(f"{n} {rng.randint(1, min(n, groups))}")
        rows.append(" ".join(str(rng.randint(-top, top)) for _ in range(n)))
    return _lines(cases, rows)


CLUSTER_LINE = CodeTask(
    key="cluster-line",
    title="Кластеры на прямой",
    difficulty="hard",
    specializations=("data-science", "data-engineering"),
    topic="dynamic-programming",
    statement=(
        "На числовой прямой отмечено n точек (точки могут совпадать). Их нужно разбить на k "
        "непустых кластеров. Разброс кластера — квадрат разности между наибольшей и наименьшей "
        "его точкой. Требуется минимизировать сумму разбросов всех кластеров.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест занимает две строки: числа n и k "
        "(1 ≤ k ≤ n ≤ 300, k ≤ 30) и n координат — целые числа от −10^6 до 10^6. Сумма значений "
        "n²·k по всем тестам одного входа не превышает 3·10^6.\n\n"
        "Для каждого теста выведите наименьшую возможную сумму разбросов."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, k = int(data[pos]), int(data[pos + 1])
    points = sorted(int(item) for item in data[pos + 2 : pos + 2 + n])
    pos += 2 + n
    previous = [(points[end - 1] - points[0]) ** 2 if end else 0 for end in range(n + 1)]
    for groups in range(2, k + 1):
        current = [0] * (n + 1)
        for end in range(groups, n + 1):
            last = points[end - 1]
            current[end] = min(
                previous[cut] + (last - points[cut]) ** 2 for cut in range(groups - 1, end)
            )
        previous = current
    print(previous[n])
""",
    brute="""import sys
from itertools import product

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, k = int(data[pos]), int(data[pos + 1])
    points = [int(item) for item in data[pos + 2 : pos + 2 + n]]
    pos += 2 + n
    best = None
    for labels in product(range(k), repeat=n):
        if len(set(labels)) < k:
            continue
        cost = 0
        for group in range(k):
            members = [point for point, label in zip(points, labels) if label == group]
            cost += (max(members) - min(members)) ** 2
        if best is None or cost < best:
            best = cost
    print(best)
""",
    small=lambda rng: _points(rng, 8, 7, 9, 3),
    sample="3\n5 2\n1 9 2 10 3\n4 1\n-5 0 7 2\n3 3\n4 4 8\n",
    hidden=lambda rng: [
        "3\n1 1\n5\n4 2\n0 0 0 0\n6 3\n1 2 3 11 12 30\n",
        _points(rng, 30, 8, 12, 4),
        _points(rng, 20, 60, 1000, 8),
        _points(rng, 2, 300, 10**6, 15, full=True),
        _points(rng, 1, 300, 50, 30, full=True),
    ],
)


def _words(rng: random.Random, cases: int, size: int, width: int, full: bool = False) -> str:
    rows = []
    for _ in range(cases):
        n, limit = (size, width) if full else (rng.randint(1, size), rng.randint(1, width))
        rows.append(f"{n} {limit}")
        rows.append(" ".join(str(rng.randint(1, max(1, min(limit, 12)))) for _ in range(n)))
    return _lines(cases, rows)


TEXT_WRAP = CodeTask(
    key="text-wrap",
    title="Ровный перенос строк",
    difficulty="hard",
    specializations=("frontend", "fullstack", "mobile"),
    topic="dynamic-programming",
    statement=(
        "Абзац из n слов нужно разбить на строки шириной W символов, не меняя порядок слов. Слова "
        "в строке разделяются ровно одним пробелом, длина строки не должна превышать W. Штраф "
        "строки — квадрат числа свободных позиций в её конце (W минус длина строки). Последняя "
        "строка абзаца не штрафуется. Требуется найти разбиение с наименьшей суммой штрафов.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест занимает две строки: числа n и W "
        "(1 ≤ n ≤ 2000, 1 ≤ W ≤ 100) и n длин слов — целые числа от 1 до W. Для каждого теста "
        "выведите наименьшую возможную сумму штрафов."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, width = int(data[pos]), int(data[pos + 1])
    words = [int(item) for item in data[pos + 2 : pos + 2 + n]]
    pos += 2 + n
    best = [0] * (n + 1)
    for start in range(n - 1, -1, -1):
        used = -1
        cheapest = None
        for end in range(start, n):
            used += words[end] + 1
            if used > width:
                break
            cost = 0 if end == n - 1 else (width - used) ** 2 + best[end + 1]
            if cheapest is None or cost < cheapest:
                cheapest = cost
        best[start] = cheapest
    print(best[0])
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, width = int(data[pos]), int(data[pos + 1])
    words = [int(item) for item in data[pos + 2 : pos + 2 + n]]
    pos += 2 + n
    best = None
    for breaks in range(1 << (n - 1)):
        lines, line = [], [words[0]]
        for index in range(1, n):
            if breaks >> (index - 1) & 1:
                lines.append(line)
                line = []
            line.append(words[index])
        lines.append(line)
        lengths = [sum(line) + len(line) - 1 for line in lines]
        if max(lengths) > width:
            continue
        cost = sum((width - length) ** 2 for length in lengths[:-1])
        if best is None or cost < best:
            best = cost
    print(best)
""",
    small=lambda rng: _words(rng, 12, 9, 10),
    sample="3\n5 10\n3 2 2 5 4\n3 4\n4 4 4\n4 7\n3 3 3 3\n",
    hidden=lambda rng: [
        "3\n1 5\n5\n2 5\n1 1\n6 6\n3 2 3 2 3 2\n",
        _words(rng, 30, 10, 12),
        _words(rng, 30, 200, 40),
        _words(rng, 5, 2000, 100, full=True),
        _words(rng, 5, 2000, 15, full=True),
    ],
)


def _terrain(
    rng: random.Random, cases: int, side: int, walls: float, costs: str, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        h, w = (side, side) if full else (rng.randint(1, side), rng.randint(1, side))
        grid = [
            ["#" if rng.random() < walls else rng.choice(costs) for _ in range(w)] for _ in range(h)
        ]
        if rng.random() < 0.9:
            grid[0][0] = rng.choice(costs)
            grid[h - 1][w - 1] = rng.choice(costs)
        rows.append(f"{h} {w}")
        rows += ["".join(row) for row in grid]
    return _lines(cases, rows)


TERRAIN_PATH = CodeTask(
    key="terrain-path",
    title="Путь по пересечённой местности",
    difficulty="hard",
    specializations=("gamedev", "mobile"),
    topic="graphs",
    statement=(
        "Карта уровня — прямоугольник из h строк и w столбцов. Цифра от 1 до 9 в клетке — цена её "
        "прохождения, «#» — стена. Юнит стоит в левой верхней клетке и должен попасть в правую "
        "нижнюю, переходя между соседними по стороне клетками без стен. Цена пути — сумма цен всех "
        "клеток пути, включая начальную и конечную.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест состоит из строки с числами h и w "
        "(1 ≤ h, w ≤ 60) и h строк карты. Сумма площадей карт одного входа не превышает 20 000. Для "
        "каждого теста выведите наименьшую цену пути или −1, если пути нет (в том числе когда "
        "начальная или конечная клетка — стена)."
    ),
    solution="""import heapq
import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    h, w = int(data[pos]), int(data[pos + 1])
    grid = data[pos + 2 : pos + 2 + h]
    pos += 2 + h
    answer = -1
    if grid[0][0] != "#":
        cost = {(0, 0): int(grid[0][0])}
        heap = [(cost[(0, 0)], 0, 0)]
        while heap:
            spent, y, x = heapq.heappop(heap)
            if spent > cost[(y, x)]:
                continue
            if y == h - 1 and x == w - 1:
                answer = spent
                break
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] != "#":
                    total = spent + int(grid[ny][nx])
                    if total < cost.get((ny, nx), total + 1):
                        cost[(ny, nx)] = total
                        heapq.heappush(heap, (total, ny, nx))
    print(answer)
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    h, w = int(data[pos]), int(data[pos + 1])
    grid = data[pos + 2 : pos + 2 + h]
    pos += 2 + h
    cost = {}
    if grid[0][0] != "#":
        cost[(0, 0)] = int(grid[0][0])
    changed = True
    while changed:
        changed = False
        for y, x in list(cost):
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] != "#":
                    total = cost[(y, x)] + int(grid[ny][nx])
                    if (ny, nx) not in cost or total < cost[(ny, nx)]:
                        cost[(ny, nx)] = total
                        changed = True
    print(cost.get((h - 1, w - 1), -1))
""",
    small=lambda rng: _terrain(rng, 10, 5, rng.choice((0.1, 0.3)), "123456789"),
    sample="3\n3 4\n1911\n1#91\n1111\n2 2\n1#\n#1\n1 1\n7\n",
    hidden=lambda rng: [
        "4\n1 1\n#\n1 3\n1#1\n2 3\n#11\n111\n3 3\n191\n191\n111\n",
        _terrain(rng, 30, 6, 0.2, "123456789"),
        _terrain(rng, 20, 30, 0.15, "123456789"),
        _terrain(rng, 5, 60, 0.18, "19", full=True),
        _terrain(rng, 5, 60, 0.05, "123456789", full=True),
    ],
)


TASKS = [
    SPLIT_BATCHES,
    CRITICAL_PATH,
    MIN_WINDOW,
    FIREWALL_RULES,
    ACCESS_PATHS,
    TOKEN_SPLIT,
    LCS_DIFF,
    MIN_TEST_SET,
    KNAPSACK_BUDGET,
    CLUSTER_LINE,
    TEXT_WRAP,
    TERRAIN_PATH,
]
