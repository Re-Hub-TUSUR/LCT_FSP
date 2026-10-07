"""Medium tasks: a standard technique and a few edge cases."""

import random

from app.seed.code_bank import CodeTask, pack


def _requests(
    rng: random.Random, count: int, clients: int, limit: int, window: int, step: int
) -> str:
    rows, now = [f"{count} {limit} {window}"], 0
    for _ in range(count):
        now += rng.randint(0, step)
        rows.append(f"{now} c{rng.randint(1, clients)}")
    return "\n".join(rows) + "\n"


RATE_LIMITER = CodeTask(
    key="rate-limiter",
    title="Ограничитель запросов",
    difficulty="medium",
    specializations=("backend", "devops", "security", "fullstack"),
    topic="logs",
    statement=(
        "Сервис ограничивает частоту запросов: запрос клиента в момент t принимается, если среди "
        "уже принятых запросов этого клиента меньше L таких, чьё время строго больше t − W. Иначе "
        "запрос отклоняется; отклонённые запросы в лимите не учитываются.\n\n"
        "В первой строке — три целых числа: число запросов N (1 ≤ N ≤ 4000), лимит L (1 ≤ L ≤ N) и "
        "длина окна W (1 ≤ W ≤ 10^9). Далее N строк в порядке неубывания времени: время запроса t "
        "(0 ≤ t ≤ 10^9) и идентификатор клиента (латинские буквы и цифры, до 8 символов). Запросы с "
        "одинаковым временем обрабатываются в порядке ввода.\n\n"
        "Выведите число отклонённых запросов."
    ),
    solution="""import sys
from collections import deque

data = sys.stdin.read().split()
n, limit, window = int(data[0]), int(data[1]), int(data[2])
accepted = {}
rejected = 0
for i in range(n):
    now, client = int(data[3 + 2 * i]), data[4 + 2 * i]
    queue = accepted.setdefault(client, deque())
    while queue and queue[0] <= now - window:
        queue.popleft()
    if len(queue) < limit:
        queue.append(now)
    else:
        rejected += 1
print(rejected)
""",
    brute="""import sys

data = sys.stdin.read().split()
n, limit, window = int(data[0]), int(data[1]), int(data[2])
accepted = []
rejected = 0
for i in range(n):
    now, client = int(data[3 + 2 * i]), data[4 + 2 * i]
    recent = [1 for moment, who in accepted if who == client and moment > now - window]
    if len(recent) < limit:
        accepted.append((now, client))
    else:
        rejected += 1
print(rejected)
""",
    small=lambda rng: _requests(
        rng, rng.randint(1, 14), 2, rng.randint(1, 3), rng.randint(1, 6), 3
    ),
    sample="6 2 10\n0 a\n3 a\n5 a\n9 b\n10 a\n12 a\n",
    hidden=lambda rng: [
        "5 1 5\n0 a\n4 a\n5 a\n5 a\n10 a\n",
        _requests(rng, 60, 3, 2, 8, 4),
        _requests(rng, 1500, 40, 5, 100, 6),
        _requests(rng, 4000, 3, 300, 10**9, 2),
        _requests(rng, 4000, 600, 2, 50, 10),
    ],
)


def _accesses(
    rng: random.Random, cases: int, capacity: int, length: int, keys: int, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        n = length if full else rng.randint(1, length)
        rows.append(f"{rng.randint(1, capacity)} {n}")
        rows.append(" ".join(str(rng.randint(1, keys)) for _ in range(n)))
    return f"{cases}\n" + "\n".join(rows) + "\n"


LRU_CACHE = CodeTask(
    key="lru-cache",
    title="Промахи LRU-кэша",
    difficulty="medium",
    specializations=("backend", "mobile", "frontend", "fullstack"),
    topic="data",
    statement=(
        "Кэш хранит не больше C ключей. При обращении к ключу, которого в кэше нет, происходит "
        "промах: ключ загружается в кэш, а если места нет, сначала вытесняется ключ, к которому "
        "дольше всего не обращались. Обращение к ключу из кэша делает его самым свежим.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Каждый тест занимает две строки: ёмкость C и "
        "число обращений n (1 ≤ C ≤ 10^5, 1 ≤ n ≤ 2000), затем n ключей — целые числа от 1 до 10^9. "
        "Для каждого теста выведите число промахов. Кэш в начале каждого теста пуст."
    ),
    solution="""import sys
from collections import OrderedDict

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    capacity, n = int(data[pos]), int(data[pos + 1])
    cache = OrderedDict()
    misses = 0
    for key in data[pos + 2 : pos + 2 + n]:
        if key in cache:
            cache.move_to_end(key)
        else:
            misses += 1
            if len(cache) == capacity:
                cache.popitem(last=False)
            cache[key] = True
    pos += 2 + n
    print(misses)
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    capacity, n = int(data[pos]), int(data[pos + 1])
    order = []
    misses = 0
    for key in data[pos + 2 : pos + 2 + n]:
        if key in order:
            order.remove(key)
        else:
            misses += 1
            if len(order) == capacity:
                order.pop(0)
        order.append(key)
    pos += 2 + n
    print(misses)
""",
    small=lambda rng: _accesses(rng, 20, 3, 12, 5),
    sample="2\n2 6\n1 2 1 3 2 1\n3 4\n5 5 5 5\n",
    hidden=lambda rng: [
        "3\n1 5\n7 7 8 7 8\n100000 3\n1 2 1\n2 7\n1 2 3 1 2 3 1\n",
        _accesses(rng, 30, 4, 40, 8),
        _accesses(rng, 30, 50, 800, 120),
        _accesses(rng, 5, 600, 2000, 1500, full=True),
    ],
)


def _deps(
    rng: random.Random, cases: int, size: int, edges: int, cyclic: float, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        order = list(range(1, n + 1))
        rng.shuffle(order)
        pairs = []
        if n > 1:
            # A chain keeps the answer from collapsing to a couple of stages.
            chain = rng.randint(0, n - 1)
            pairs += [(order[i + 1], order[i]) for i in range(chain)]
            for _ in range(rng.randint(0, max(0, min(edges, 3 * n) - chain))):
                low, high = sorted(rng.sample(range(n), 2))
                pairs.append((order[high], order[low]))
        if rng.random() < cyclic:
            pairs.append((rng.randint(1, n), rng.randint(1, n)))
        rng.shuffle(pairs)
        rows.append(f"{n} {len(pairs)}")
        rows += [f"{a} {b}" for a, b in pairs]
    return f"{cases}\n" + "\n".join(rows) + "\n"


BUILD_STAGES = CodeTask(
    key="build-stages",
    title="Стадии сборки",
    difficulty="medium",
    specializations=("devops", "backend", "data-engineering"),
    topic="graphs",
    statement=(
        "Конвейер состоит из n задач с номерами от 1 до n. Задачу можно запустить, когда завершены "
        "все задачи, от которых она зависит. Конвейер выполняется стадиями: в одной стадии "
        "одновременно запускаются все задачи, зависимости которых завершены в предыдущих стадиях.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 40). Тест начинается строкой с числами n и m "
        "(1 ≤ n ≤ 1000, 0 ≤ m ≤ 2000), далее m строк «a b»: задача a зависит от задачи b. Одна и та "
        "же зависимость может повторяться, задача может зависеть сама от себя.\n\n"
        "Для каждого теста выведите минимальное число стадий, за которое выполнятся все задачи, или "
        "CYCLE, если из-за циклической зависимости выполнить все задачи невозможно."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    pos += 2
    children = [[] for _ in range(n + 1)]
    waiting = [0] * (n + 1)
    for _ in range(m):
        a, b = int(data[pos]), int(data[pos + 1])
        pos += 2
        children[b].append(a)
        waiting[a] += 1
    layer = [task for task in range(1, n + 1) if waiting[task] == 0]
    done = stages = 0
    while layer:
        stages += 1
        done += len(layer)
        following = []
        for task in layer:
            for child in children[task]:
                waiting[child] -= 1
                if waiting[child] == 0:
                    following.append(child)
        layer = following
    print(stages if done == n else "CYCLE")
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    pos += 2
    needs = {task: set() for task in range(1, n + 1)}
    for _ in range(m):
        needs[int(data[pos])].add(int(data[pos + 1]))
        pos += 2
    done = set()
    stages = 0
    while len(done) < n:
        ready = [task for task in needs if task not in done and needs[task] <= done]
        if not ready:
            break
        done.update(ready)
        stages += 1
    print(stages if len(done) == n else "CYCLE")
""",
    small=lambda rng: _deps(rng, 15, 7, 12, 0.35),
    sample="3\n4 3\n2 1\n3 1\n4 2\n3 3\n1 2\n2 3\n3 1\n2 0\n",
    hidden=lambda rng: [
        "4\n1 0\n1 1\n1 1\n3 4\n2 1\n2 1\n3 2\n3 1\n5 4\n2 1\n3 2\n4 3\n5 4\n",
        _deps(rng, 40, 8, 14, 0.3),
        _deps(rng, 30, 80, 120, 0.15),
        _deps(rng, 3, 1000, 1999, 0.0, full=True),
    ],
)


def _ip(value: int) -> str:
    return ".".join(str(value >> shift & 255) for shift in (24, 16, 8, 0))


def _cidr(rng: random.Random, cases: int, queries: int) -> str:
    rows = []
    for _ in range(cases):
        prefix = rng.choice((0, 1, 7, 8, 9, 15, 16, 20, 23, 24, 25, 30, 31, 32, rng.randint(0, 32)))
        base = rng.getrandbits(32)
        rows.append(f"{_ip(base)}/{prefix}")
        q = rng.randint(1, queries)
        rows.append(str(q))
        for _ in range(q):
            if rng.random() < 0.6:
                flips = rng.getrandbits(32) >> min(31, max(0, prefix - rng.choice((0, 0, 1, 2))))
                rows.append(_ip(base ^ flips))
            else:
                rows.append(_ip(rng.getrandbits(32)))
    return f"{cases}\n" + "\n".join(rows) + "\n"


CIDR_COUNT = CodeTask(
    key="cidr-count",
    title="Адреса в подсети",
    difficulty="medium",
    specializations=("devops", "security"),
    topic="algorithms",
    statement=(
        "Подсеть записана как A.B.C.D/P: адрес принадлежит ей, если его первые P бит совпадают с "
        "первыми P битами адреса A.B.C.D (адрес — 32 бита, старший октет первый). В записи подсети "
        "младшие 32 − P бит могут быть ненулевыми — они не учитываются. При P = 0 подсети "
        "принадлежит любой адрес.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест состоит из строки с подсетью "
        "(0 ≤ P ≤ 32), строки с числом адресов q (1 ≤ q ≤ 100) и q строк с корректными "
        "IPv4-адресами. Для каждого теста выведите, сколько из этих адресов принадлежит подсети."
    ),
    solution="""import sys


def number(address):
    value = 0
    for part in address.split("."):
        value = value * 256 + int(part)
    return value


data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    address, prefix = data[pos].split("/")
    shift = 32 - int(prefix)
    network = number(address) >> shift
    q = int(data[pos + 1])
    print(sum(number(item) >> shift == network for item in data[pos + 2 : pos + 2 + q]))
    pos += 2 + q
""",
    brute="""import sys


def bits(address):
    return "".join(format(int(part), "08b") for part in address.split("."))


data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    address, prefix = data[pos].split("/")
    head = bits(address)[: int(prefix)]
    q = int(data[pos + 1])
    print(sum(bits(item).startswith(head) for item in data[pos + 2 : pos + 2 + q]))
    pos += 2 + q
""",
    small=lambda rng: _cidr(rng, 10, 8),
    sample=(
        "2\n10.20.0.0/16\n4\n10.20.0.1\n10.20.255.255\n10.21.0.0\n192.168.1.1\n"
        "192.168.1.77/24\n3\n192.168.1.0\n192.168.2.77\n192.168.1.255\n"
    ),
    hidden=lambda rng: [
        "3\n1.2.3.4/0\n2\n255.255.255.255\n0.0.0.0\n1.2.3.4/32\n3\n1.2.3.4\n1.2.3.5\n1.2.3.4\n"
        "128.0.0.0/1\n3\n127.255.255.255\n128.0.0.0\n255.0.0.1\n",
        _cidr(rng, 30, 10),
        _cidr(rng, 30, 100),
        _cidr(rng, 30, 100),
    ],
)


def _roles(rng: random.Random, n: int, m: int, grants: int, perms: int, queries: int) -> str:
    rows = [f"{n} {m} {grants} {queries}"]
    rows += [f"{rng.randint(1, n)} {rng.randint(1, n)}" for _ in range(m)]
    rows += [f"{rng.randint(1, n)} {rng.randint(1, perms)}" for _ in range(grants)]
    rows += [f"{rng.randint(1, n)} {rng.randint(1, perms)}" for _ in range(queries)]
    return "\n".join(rows) + "\n"


ROLE_ACCESS = CodeTask(
    key="role-access",
    title="Наследование ролей",
    difficulty="medium",
    specializations=("security", "backend"),
    topic="graphs",
    statement=(
        "В системе n ролей с номерами от 1 до n. Роль может наследовать другую: тогда она получает "
        "все её права, включая унаследованные той по цепочке. Наследование может образовывать "
        "циклы — роли одного цикла получают права друг друга.\n\n"
        "В первой строке — четыре числа: n, m, g и q (1 ≤ n ≤ 300, 0 ≤ m ≤ 1500, 0 ≤ g ≤ 2000, "
        "1 ≤ q ≤ 3000). Далее m строк «a b»: роль a наследует роль b. Затем g строк «r p»: роли r "
        "напрямую выдано право с номером p (1 ≤ p ≤ 10^9). Затем q строк «r p» — запросы: есть ли у "
        "роли r право p.\n\n"
        "Выведите число запросов, на которые ответ «да»."
    ),
    solution="""import sys

data = sys.stdin.read().split()
n, m, g, q = (int(item) for item in data[:4])
pos = 4
parents = [[] for _ in range(n + 1)]
for _ in range(m):
    parents[int(data[pos])].append(int(data[pos + 1]))
    pos += 2
direct = [set() for _ in range(n + 1)]
for _ in range(g):
    direct[int(data[pos])].add(data[pos + 1])
    pos += 2
rights = {}
allowed = 0
for _ in range(q):
    role, right = int(data[pos]), data[pos + 1]
    pos += 2
    if role not in rights:
        seen = {role}
        stack = [role]
        total = set()
        while stack:
            current = stack.pop()
            total |= direct[current]
            for parent in parents[current]:
                if parent not in seen:
                    seen.add(parent)
                    stack.append(parent)
        rights[role] = total
    allowed += right in rights[role]
print(allowed)
""",
    brute="""import sys

data = sys.stdin.read().split()
n, m, g, q = (int(item) for item in data[:4])
pos = 4
links = []
for _ in range(m):
    links.append((int(data[pos]), int(data[pos + 1])))
    pos += 2
rights = [set() for _ in range(n + 1)]
for _ in range(g):
    rights[int(data[pos])].add(data[pos + 1])
    pos += 2
changed = True
while changed:
    changed = False
    for child, parent in links:
        if not rights[parent] <= rights[child]:
            rights[child] |= rights[parent]
            changed = True
allowed = 0
for _ in range(q):
    allowed += data[pos + 1] in rights[int(data[pos])]
    pos += 2
print(allowed)
""",
    small=lambda rng: _roles(rng, rng.randint(1, 6), rng.randint(0, 8), rng.randint(0, 6), 4, 12),
    sample="4 3 3 5\n2 1\n3 2\n4 4\n1 10\n2 20\n4 30\n3 10\n3 20\n1 20\n4 30\n2 30\n",
    hidden=lambda rng: [
        "3 3 2 6\n1 2\n2 3\n3 1\n1 5\n3 7\n1 7\n2 5\n3 5\n2 7\n1 6\n3 8\n",
        _roles(rng, 8, 10, 10, 6, 60),
        _roles(rng, 120, 200, 400, 60, 1500),
        _roles(rng, 300, 1500, 2000, 900, 3000),
        _roles(rng, 300, 280, 2000, 40, 3000),
    ],
)


def _durations(
    rng: random.Random, cases: int, size: int, workers: int, top: int, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        rows.append(f"{n} {rng.randint(1, workers)}")
        rows.append(" ".join(str(rng.randint(1, top)) for _ in range(n)))
    return f"{cases}\n" + "\n".join(rows) + "\n"


TEST_SCHEDULE = CodeTask(
    key="test-schedule",
    title="Раскладка тестов по исполнителям",
    difficulty="medium",
    specializations=("qa", "devops"),
    topic="algorithms",
    statement=(
        "Набор из n автотестов запускают на w одинаковых исполнителях. Раскладывают так: тесты "
        "перебирают в порядке убывания длительности и очередной тест отдают исполнителю, у которого "
        "сейчас наименьшая суммарная длительность назначенных тестов. Каждый исполнитель выполняет "
        "свои тесты подряд без пауз.\n\n"
        "В первой строке — число тестов входных данных T (1 ≤ T ≤ 40). Каждый занимает две строки: "
        "числа n и w (1 ≤ n ≤ 2000, 1 ≤ w ≤ 2000), затем n длительностей — целые числа от 1 до 10^6. "
        "Для каждого выведите время, за которое при такой раскладке завершится весь прогон."
    ),
    solution="""import heapq
import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, workers = int(data[pos]), int(data[pos + 1])
    durations = sorted((int(item) for item in data[pos + 2 : pos + 2 + n]), reverse=True)
    pos += 2 + n
    loads = [0] * min(workers, n)
    for duration in durations:
        heapq.heapreplace(loads, loads[0] + duration)
    print(max(loads))
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, workers = int(data[pos]), int(data[pos + 1])
    durations = sorted((int(item) for item in data[pos + 2 : pos + 2 + n]), reverse=True)
    pos += 2 + n
    loads = [0] * workers
    for duration in durations:
        loads[loads.index(min(loads))] += duration
    print(max(loads))
""",
    small=lambda rng: _durations(rng, 20, 9, 4, 9),
    sample="3\n5 2\n3 8 2 5 4\n3 5\n7 1 2\n4 1\n1 2 3 4\n",
    hidden=lambda rng: [
        "3\n1 1\n9\n6 3\n5 5 5 5 5 5\n7 3\n9 8 7 6 5 4 3\n",
        _durations(rng, 40, 12, 5, 20),
        _durations(rng, 30, 400, 30, 1000),
        _durations(rng, 4, 2000, 300, 10**6, full=True),
    ],
)


def _events(rng: random.Random, count: int, users: int, gap: int, span: int) -> str:
    rows = [f"{count} {gap}"]
    rows += [f"u{rng.randint(1, users)} {rng.randint(0, span)}" for _ in range(count)]
    return "\n".join(rows) + "\n"


SESSIONS = CodeTask(
    key="sessions",
    title="Подсчёт сессий",
    difficulty="medium",
    specializations=("data-engineering", "data-science"),
    topic="data",
    statement=(
        "События пользователей объединяют в сессии: событие продолжает сессию пользователя, если "
        "с его предыдущего по времени события прошло не больше G секунд, иначе начинает новую. "
        "Первое событие пользователя всегда начинает сессию.\n\n"
        "В первой строке — число событий N (1 ≤ N ≤ 3000) и число G (0 ≤ G ≤ 10^9). Далее N строк в "
        "произвольном порядке: идентификатор пользователя (латинские буквы и цифры, до 8 символов) "
        "и время события в секундах (от 0 до 10^9). У пользователя может быть несколько событий с "
        "одним временем.\n\n"
        "Выведите общее число сессий всех пользователей."
    ),
    solution="""import sys

data = sys.stdin.read().split()
n, gap = int(data[0]), int(data[1])
times = {}
for i in range(n):
    times.setdefault(data[2 + 2 * i], []).append(int(data[3 + 2 * i]))
sessions = 0
for moments in times.values():
    moments.sort()
    sessions += 1 + sum(later - earlier > gap for earlier, later in zip(moments, moments[1:]))
print(sessions)
""",
    brute="""import sys

data = sys.stdin.read().split()
n, gap = int(data[0]), int(data[1])
events = sorted((int(data[3 + 2 * i]), data[2 + 2 * i]) for i in range(n))
last = {}
sessions = 0
for moment, user in events:
    if user not in last or moment - last[user] > gap:
        sessions += 1
    last[user] = moment
print(sessions)
""",
    small=lambda rng: _events(rng, rng.randint(1, 12), 3, rng.randint(0, 4), 20),
    sample="6 30\nann 100\nbob 10\nann 10\nann 131\nbob 40\nann 35\n",
    hidden=lambda rng: [
        "5 0\na 5\na 5\na 6\nb 5\na 5\n",
        _events(rng, 50, 4, 5, 200),
        _events(rng, 2000, 150, 60, 20000),
        _events(rng, 3000, 12, 1000, 10**9),
        _events(rng, 3000, 2500, 10**9, 10**9),
    ],
)


def _labels(rng: random.Random, count: int, size: int, full: bool = False) -> str:
    rows = []
    for _ in range(count):
        n = size if full else rng.randint(1, size)
        bias = rng.choice((0.0, 0.1, 0.5, 0.9, 1.0))
        truth = "".join("1" if rng.random() < bias else "0" for _ in range(n))
        guess = "".join(ch if rng.random() < 0.7 else rng.choice("01") for ch in truth)
        rows.append(f"{truth} {guess}")
    return pack(rows)


F1_SCORE = CodeTask(
    key="f1-score",
    title="Матрица ошибок и F1",
    difficulty="medium",
    specializations=("data-science",),
    topic="statistics",
    statement=(
        "Бинарный классификатор проверили на n объектах. Даны две строки длины n из символов 0 и 1: "
        "истинные метки и предсказания. Обозначим TP — число объектов, где и метка, и предсказание "
        "равны 1; FP — метка 0, предсказание 1; FN — метка 1, предсказание 0; TN — оба равны 0. "
        "F1-мера равна 2·TP / (2·TP + FP + FN); если знаменатель равен нулю, F1 считается равной 0.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 25). В каждой из следующих T строк — через пробел "
        "строка меток и строка предсказаний одинаковой длины (1 ≤ n ≤ 1500). Для каждого теста "
        "выведите в одной строке числа TP, FP, FN, TN и F1 в виде несократимой дроби p/q. Нулевую "
        "F1 выводите как 0/1."
    ),
    solution="""import sys
from math import gcd

data = sys.stdin.read().split()
for i in range(int(data[0])):
    truth, guess = data[1 + 2 * i], data[2 + 2 * i]
    tp = fp = fn = tn = 0
    for real, predicted in zip(truth, guess):
        if predicted == "1":
            if real == "1":
                tp += 1
            else:
                fp += 1
        elif real == "1":
            fn += 1
        else:
            tn += 1
    top, bottom = 2 * tp, 2 * tp + fp + fn
    if top == 0:
        top, bottom = 0, 1
    else:
        common = gcd(top, bottom)
        top, bottom = top // common, bottom // common
    print(tp, fp, fn, tn, f"{top}/{bottom}")
""",
    sample=pack(["1100 1010", "111 111", "000 000", "10 01"]),
    hidden=lambda rng: [
        pack(["1 1", "0 0", "1 0", "0 1", "1111 1110", "110 111", "111000 111111"]),
        _labels(rng, 25, 12),
        _labels(rng, 25, 300),
        _labels(rng, 25, 1500),
    ],
)


def _keys(rng: random.Random, cases: int, size: int, spread: int, full: bool = False) -> str:
    rows = []
    for _ in range(cases):
        n, m = (size, size) if full else (rng.randint(1, size), rng.randint(1, size))
        rows.append(f"{n} {m}")
        rows.append(" ".join(str(rng.randint(1, spread)) for _ in range(n)))
        rows.append(" ".join(str(rng.randint(1, spread)) for _ in range(m)))
    return f"{cases}\n" + "\n".join(rows) + "\n"


JOIN_SIZE = CodeTask(
    key="join-size",
    title="Размер соединения таблиц",
    difficulty="medium",
    specializations=("data-engineering", "backend", "data-science"),
    topic="data",
    statement=(
        "Две таблицы соединяют по ключу. INNER JOIN даёт по строке на каждую пару строк левой и "
        "правой таблицы с равными ключами. LEFT JOIN дополнительно даёт по одной строке на каждую "
        "строку левой таблицы, для ключа которой в правой таблице пары нет.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест занимает три строки: числа строк n и m "
        "в левой и правой таблицах (1 ≤ n, m ≤ 2000), n ключей левой таблицы и m ключей правой — "
        "целые числа от 1 до 10^9. Для каждого теста выведите через пробел число строк в результате "
        "INNER JOIN и число строк в результате LEFT JOIN."
    ),
    solution="""import sys
from collections import Counter

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    left = data[pos + 2 : pos + 2 + n]
    right = Counter(data[pos + 2 + n : pos + 2 + n + m])
    pos += 2 + n + m
    inner = sum(right[key] for key in left)
    print(inner, inner + sum(key not in right for key in left))
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n, m = int(data[pos]), int(data[pos + 1])
    left = data[pos + 2 : pos + 2 + n]
    right = data[pos + 2 + n : pos + 2 + n + m]
    pos += 2 + n + m
    inner = outer = 0
    for key in left:
        pairs = sum(1 for other in right if other == key)
        inner += pairs
        outer += pairs or 1
    print(inner, outer)
""",
    small=lambda rng: _keys(rng, 15, 7, 4),
    sample="2\n4 3\n1 2 2 5\n2 2 7\n2 2\n9 9\n9 9\n",
    hidden=lambda rng: [
        "3\n1 1\n1\n2\n3 3\n4 4 4\n4 4 4\n2 4\n1 2\n3 4 5 6\n",
        _keys(rng, 30, 10, 5),
        _keys(rng, 20, 400, 80),
        _keys(rng, 3, 2000, 20, full=True),
        _keys(rng, 1, 2000, 10**9, full=True),
    ],
)

TAG_NAMES = ("a", "b", "p", "div", "ul", "li", "h1", "span")


def _markup(rng: random.Random, budget: int, depth: int) -> str:
    parts = []
    while budget > 0:
        name = rng.choice(TAG_NAMES)
        roll = rng.random()
        if roll < 0.25 or depth == 0:
            parts.append(f"<{name}/>" if roll < 0.15 else f"<{name}></{name}>")
            budget -= 1
        else:
            inner = rng.randint(0, budget - 1)
            parts.append(f"<{name}>{_markup(rng, inner, depth - 1)}</{name}>")
            budget -= inner + 1
    return "".join(parts)


def _spoil(rng: random.Random, text: str) -> str:
    tags = text.replace(">", ">\n").split()
    kind = rng.randint(0, 3)
    slot = rng.randrange(len(tags))
    if kind == 0:
        tags.pop(slot)
    elif kind == 1:
        tags.insert(slot, rng.choice(("</b>", "<b>", "</div>")))
    elif kind == 2 and len(tags) > 1:
        other = rng.randrange(len(tags))
        tags[slot], tags[other] = tags[other], tags[slot]
    return "".join(tags) or "<a>"


def _pages_markup(rng: random.Random, count: int, budget: int, depth: int) -> str:
    rows = []
    for _ in range(count):
        text = _markup(rng, rng.randint(1, budget), depth)
        rows.append(_spoil(rng, text) if rng.random() < 0.45 else text)
    return pack(rows)


NESTED_TAGS = CodeTask(
    key="nested-tags",
    title="Вложенность разметки",
    difficulty="medium",
    specializations=("frontend", "fullstack", "mobile", "qa"),
    topic="strings",
    statement=(
        "Разметка — строка без пробелов из тегов трёх видов: открывающий <имя>, закрывающий </имя> "
        "и самозакрывающийся <имя/>. Имя состоит из строчных латинских букв и цифр. Разметка "
        "корректна, если каждый закрывающий тег закрывает последний ещё не закрытый открывающий тег "
        "с тем же именем и в конце незакрытых тегов не остаётся.\n\n"
        "Глубина тега — число открытых в этот момент тегов, считая его самого; самозакрывающийся "
        "тег тоже считается.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 60). В каждой из следующих T строк — непустая "
        "разметка длиной до 1200 символов, состоящая только из тегов описанного вида. Для каждой "
        "выведите наибольшую глубину тега, если разметка корректна, иначе INVALID."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for text in data[1 : int(data[0]) + 1]:
    stack = []
    deepest = 0
    valid = True
    for tag in text[1:-1].split("><"):
        if tag.endswith("/"):
            deepest = max(deepest, len(stack) + 1)
        elif tag.startswith("/"):
            if not stack or stack.pop() != tag[1:]:
                valid = False
                break
        else:
            stack.append(tag)
            deepest = max(deepest, len(stack))
    print(deepest if valid and not stack else "INVALID")
""",
    brute="""import re
import sys

data = sys.stdin.read().split()
for text in data[1 : int(data[0]) + 1]:
    current = re.sub(r"<(\\w+)/>", r"{1}", text)
    best = 0
    changed = True
    while changed:
        changed = False
        match = re.search(r"<(\\w+)>((?:\\{\\d+\\})*)</\\1>", current)
        if match:
            inner = [int(item) for item in re.findall(r"\\{(\\d+)\\}", match.group(2))]
            current = current[: match.start()] + "{%d}" % (max(inner, default=0) + 1) + current[match.end() :]
            changed = True
    if re.fullmatch(r"(?:\\{\\d+\\})+", current):
        print(max(int(item) for item in re.findall(r"\\{(\\d+)\\}", current)))
    else:
        print("INVALID")
""",
    small=lambda rng: _pages_markup(rng, 20, 6, 3),
    sample=pack(["<div><p></p><br/></div>", "<a><b></a></b>", "<img/>", "<ul><li></li>"]),
    hidden=lambda rng: [
        pack(
            [
                "<a></a>",
                "</a><a>",
                "<a>",
                "</a>",
                "<a/><b/>",
                "<a><a><a></a></a></a>",
                "<a></b>",
                "<h1></h1><h1></h2>",
            ]
        ),
        _pages_markup(rng, 60, 8, 4),
        _pages_markup(rng, 60, 40, 12),
        _pages_markup(rng, 40, 80, 40),
    ],
)


def _selector(rng: random.Random, size: int) -> str:
    compounds = []
    for _ in range(rng.randint(1, size)):
        head = rng.choice(("div", "a", "li", "p", "span", "*", ""))
        tail = "".join(
            rng.choice((".card", ".link", ".active", "#main", "#nav"))
            for _ in range(rng.randint(0, 3))
        )
        compounds.append(head + tail or "*")
    return "".join(
        part + (rng.choice((" ", " > ", ">")) if index < len(compounds) - 1 else "")
        for index, part in enumerate(compounds)
    )


def _sheets(rng: random.Random, cases: int, rules: int, size: int) -> str:
    rows = []
    for _ in range(cases):
        n = rng.randint(1, rules)
        rows.append(str(n))
        rows += [_selector(rng, size) for _ in range(n)]
    return f"{cases}\n" + "\n".join(rows) + "\n"


CSS_SPECIFICITY = CodeTask(
    key="css-specificity",
    title="Победивший селектор",
    difficulty="medium",
    specializations=("frontend", "fullstack"),
    topic="strings",
    statement=(
        "Селектор состоит из одного или нескольких составных частей, разделённых пробелами или "
        "знаком «>» (вокруг него могут быть пробелы). Составная часть — это необязательное имя тега "
        "(строчные латинские буквы) или «*», за которым идут ноль или больше классов вида .имя и "
        "идентификаторов вида #имя.\n\n"
        "Специфичность селектора — тройка (I, C, E): число идентификаторов, число классов и число "
        "имён тегов во всех его частях; «*» ни в одно число не входит. Тройки сравнивают сначала по "
        "I, затем по C, затем по E. Из нескольких правил побеждает селектор с наибольшей "
        "специфичностью, а при равенстве — записанный позже.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест состоит из строки с числом селекторов "
        "n (1 ≤ n ≤ 40) и n строк с селекторами длиной до 150 символов. Для каждого теста выведите "
        "через пробел номер победившего селектора (нумерация с 1) и его I, C и E."
    ),
    solution="""import sys

lines = sys.stdin.read().split("\\n")
pos = 1
for _ in range(int(lines[0])):
    n = int(lines[pos])
    best, winner = (-1, -1, -1), 0
    for index in range(1, n + 1):
        selector = lines[pos + index]
        tags = sum(part[0].isalpha() for part in selector.replace(">", " ").split())
        rank = (selector.count("#"), selector.count("."), tags)
        if rank >= best:
            best, winner = rank, index
    pos += n + 1
    print(winner, *best)
""",
    sample="2\n3\ndiv.card a\n#main\nli.active.link > a\n2\np\nspan\n",
    hidden=lambda rng: [
        "3\n1\n*\n3\n*.card\n.link\ndiv\n2\na#main.card>li\n#nav.active   >  p\n",
        _sheets(rng, 30, 6, 2),
        _sheets(rng, 30, 40, 3),
        _sheets(rng, 30, 40, 4),
    ],
)


def _edits(rng: random.Random, cases: int, size: int, cap: int, full: bool = False) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        rows.append(str(n))
        length = 0
        for _ in range(n):
            roll = rng.random()
            if roll < 0.5 and length < cap:
                rows.append(f"type {rng.choice('abcxyz')}")
                length += 1
            elif roll < 0.8:
                rows.append("undo")
                length = max(0, length - 1)
            else:
                rows.append("redo")
                length = min(cap, length + 1)
    return f"{cases}\n" + "\n".join(rows) + "\n"


UNDO_REDO = CodeTask(
    key="undo-redo",
    title="Отмена и повтор",
    difficulty="medium",
    specializations=("frontend", "mobile", "gamedev"),
    topic="strings",
    statement=(
        "Редактор хранит текст и поддерживает три команды. «type c» дописывает в конец текста "
        "букву c. «undo» отменяет последнюю ещё не отменённую команду type. «redo» возвращает "
        "последнюю отменённую букву. Любая команда type очищает список отменённых букв. Команды "
        "undo и redo, которым нечего отменять или возвращать, игнорируются.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 25). Тест состоит из строки с числом команд n "
        "(1 ≤ n ≤ 2000) и n строк с командами; c — строчная латинская буква. Гарантируется, что "
        "длина текста никогда не превышает 30. Для каждого теста выведите итоговый текст или EMPTY, "
        "если он пуст. В начале каждого теста текст пуст."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n = int(data[pos])
    pos += 1
    text, undone = [], []
    for _ in range(n):
        command = data[pos]
        pos += 1
        if command == "type":
            text.append(data[pos])
            pos += 1
            undone.clear()
        elif command == "undo":
            if text:
                undone.append(text.pop())
        elif undone:
            text.append(undone.pop())
    print("".join(text) or "EMPTY")
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n = int(data[pos])
    pos += 1
    states, current = [""], 0
    for _ in range(n):
        command = data[pos]
        pos += 1
        if command == "type":
            states = states[: current + 1] + [states[current] + data[pos]]
            current += 1
            pos += 1
        elif command == "undo":
            current = max(0, current - 1)
        else:
            current = min(len(states) - 1, current + 1)
    print(states[current] or "EMPTY")
""",
    small=lambda rng: _edits(rng, 15, 12, 30),
    sample="3\n5\ntype a\ntype b\nundo\ntype c\nredo\n4\ntype x\nundo\nundo\nredo\n2\nundo\nredo\n",
    hidden=lambda rng: [
        "3\n3\ntype a\nundo\nredo\n6\ntype a\ntype b\nundo\nundo\nredo\ntype z\n3\ntype q\nundo\nundo\n",
        _edits(rng, 25, 20, 30),
        _edits(rng, 25, 300, 30),
        _edits(rng, 4, 2000, 30, full=True),
    ],
)


def _grids(rng: random.Random, cases: int, side: int, fill: float, full: bool = False) -> str:
    rows = []
    for _ in range(cases):
        h, w = (side, side) if full else (rng.randint(1, side), rng.randint(1, side))
        rows.append(f"{h} {w}")
        rows += ["".join("#" if rng.random() < fill else "." for _ in range(w)) for _ in range(h)]
    return f"{cases}\n" + "\n".join(rows) + "\n"


ISLANDS = CodeTask(
    key="islands",
    title="Острова на карте",
    difficulty="medium",
    specializations=("gamedev", "data-science", "mobile"),
    topic="graphs",
    statement=(
        "Карта — прямоугольник из h строк и w столбцов. Символ «#» обозначает сушу, «.» — воду. "
        "Остров — наибольшая по включению группа клеток суши, в которой из любой клетки можно дойти "
        "до любой другой, переходя между соседними по стороне клетками суши.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест состоит из строки с числами h и w "
        "(1 ≤ h, w ≤ 60) и h строк карты. Для каждого теста выведите через пробел число островов и "
        "площадь наибольшего из них; если суши нет, выведите «0 0»."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    h, w = int(data[pos]), int(data[pos + 1])
    grid = [list(row) for row in data[pos + 2 : pos + 2 + h]]
    pos += 2 + h
    count = largest = 0
    for top in range(h):
        for left in range(w):
            if grid[top][left] != "#":
                continue
            count += 1
            grid[top][left] = "."
            stack = [(top, left)]
            size = 0
            while stack:
                y, x = stack.pop()
                size += 1
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] == "#":
                        grid[ny][nx] = "."
                        stack.append((ny, nx))
            largest = max(largest, size)
    print(count, largest)
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    h, w = int(data[pos]), int(data[pos + 1])
    grid = data[pos + 2 : pos + 2 + h]
    pos += 2 + h
    label = {(y, x): y * w + x for y in range(h) for x in range(w) if grid[y][x] == "#"}
    changed = True
    while changed:
        changed = False
        for y, x in label:
            for cell in ((y + 1, x), (y, x + 1)):
                if cell in label and label[cell] != label[(y, x)]:
                    label[cell] = label[(y, x)] = min(label[cell], label[(y, x)])
                    changed = True
    sizes = {}
    for value in label.values():
        sizes[value] = sizes.get(value, 0) + 1
    print(len(sizes), max(sizes.values(), default=0))
""",
    small=lambda rng: _grids(rng, 12, 5, rng.choice((0.3, 0.5, 0.7))),
    sample="2\n3 5\n##..#\n#...#\n..#..\n2 2\n..\n..\n",
    hidden=lambda rng: [
        "4\n1 1\n#\n1 1\n.\n3 3\n#.#\n.#.\n#.#\n2 4\n####\n####\n",
        _grids(rng, 30, 6, 0.5),
        _grids(rng, 30, 30, 0.55),
        _grids(rng, 12, 60, 0.62, full=True),
        _grids(rng, 12, 60, 0.97, full=True),
    ],
)


def _gems(rng: random.Random, count: int, length: int, kinds: str) -> str:
    rows = []
    for _ in range(count):
        row: list[str] = []
        while len(row) < rng.randint(1, length):
            row += [rng.choice(kinds)] * rng.choice((1, 1, 2, 2, 3))
        rows.append("".join(row[:length]))
    return pack(rows)


MATCH_THREE = CodeTask(
    key="match-three",
    title="Три в ряд",
    difficulty="medium",
    specializations=("gamedev", "frontend", "mobile"),
    topic="strings",
    statement=(
        "Камни разных цветов лежат в один ряд; цвет камня — строчная латинская буква. Пока в ряду "
        "есть три или больше одинаковых камня подряд, выполняется ход: выбирается самая левая "
        "группа одинаковых камней подряд длиной не меньше трёх, она целиком (со всеми соседними "
        "камнями того же цвета) исчезает, а оставшиеся части ряда смыкаются.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 60). В каждой из следующих T строк — ряд камней "
        "длиной от 1 до 900. Для каждого ряда выведите, сколько камней останется, когда ходы "
        "закончатся."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for row in data[1 : int(data[0]) + 1]:
    stack = []
    for stone in row + "#":
        if stack and stack[-1][0] == stone:
            stack[-1][1] += 1
            continue
        if stack and stack[-1][1] >= 3:
            stack.pop()
            if stack and stack[-1][0] == stone:
                stack[-1][1] += 1
                continue
        stack.append([stone, 1])
    print(sum(count for _, count in stack) - 1)
""",
    brute="""import re
import sys

data = sys.stdin.read().split()
for row in data[1 : int(data[0]) + 1]:
    while True:
        match = re.search(r"(.)\\1\\1+", row)
        if not match:
            break
        row = row[: match.start()] + row[match.end() :]
    print(len(row))
""",
    small=lambda rng: _gems(rng, 25, 14, "ab" if rng.random() < 0.5 else "abc"),
    sample=pack(["aabbbaa", "abc", "aaabbbccc", "abbbaab"]),
    hidden=lambda rng: [
        pack(["a", "aa", "aaa", "aaaa", "abbba", "aabbbaab", "abccbbbcca", "aabbccddd"]),
        _gems(rng, 60, 20, "ab"),
        _gems(rng, 60, 300, "abc"),
        _gems(rng, 60, 900, "ab"),
        _gems(rng, 60, 900, "abcd"),
    ],
)


def _jobs(
    rng: random.Random, cases: int, size: int, span: int, length: int, full: bool = False
) -> str:
    rows = []
    for _ in range(cases):
        n = size if full else rng.randint(1, size)
        rows.append(str(n))
        for _ in range(n):
            start = rng.randint(0, span)
            rows.append(f"{start} {start + rng.randint(1, length)}")
    return f"{cases}\n" + "\n".join(rows) + "\n"


PEAK_LOAD = CodeTask(
    key="peak-load",
    title="Пиковая нагрузка",
    difficulty="medium",
    specializations=("qa", "devops", "backend", "data-engineering"),
    topic="algorithms",
    statement=(
        "Каждая задача занимает исполнителя с момента start до момента end, не включая end: "
        "задача, которая заканчивается в момент t, и задача, которая в этот момент начинается, "
        "одновременно не выполняются.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 30). Тест состоит из строки с числом задач n "
        "(1 ≤ n ≤ 2000) и n строк с целыми числами start и end (0 ≤ start < end ≤ 10^9). Для каждого "
        "теста выведите наибольшее число задач, выполнявшихся одновременно."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n = int(data[pos])
    points = []
    for i in range(n):
        points.append((int(data[pos + 1 + 2 * i]), 1))
        points.append((int(data[pos + 2 + 2 * i]), -1))
    pos += 1 + 2 * n
    points.sort()
    running = peak = 0
    for _, change in points:
        running += change
        peak = max(peak, running)
    print(peak)
""",
    brute="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n = int(data[pos])
    jobs = [(int(data[pos + 1 + 2 * i]), int(data[pos + 2 + 2 * i])) for i in range(n)]
    pos += 1 + 2 * n
    print(max(sum(1 for start, end in jobs if start <= moment < end) for moment, _ in jobs))
""",
    small=lambda rng: _jobs(rng, 15, 8, 8, 5),
    sample="2\n4\n1 5\n2 6\n5 9\n6 7\n2\n0 3\n3 8\n",
    hidden=lambda rng: [
        "3\n1\n0 1\n3\n5 6\n5 6\n5 6\n4\n0 10\n1 2\n2 3\n3 4\n",
        _jobs(rng, 30, 10, 10, 6),
        _jobs(rng, 20, 200, 1000, 200),
        _jobs(rng, 1, 2000, 10**9 - 10**8, 10**8, full=True),
        _jobs(rng, 3, 2000, 300, 300, full=True),
    ],
)


TASKS = [
    RATE_LIMITER,
    LRU_CACHE,
    BUILD_STAGES,
    CIDR_COUNT,
    ROLE_ACCESS,
    TEST_SCHEDULE,
    SESSIONS,
    F1_SCORE,
    JOIN_SIZE,
    NESTED_TAGS,
    CSS_SPECIFICITY,
    UNDO_REDO,
    ISLANDS,
    MATCH_THREE,
    PEAK_LOAD,
]
