"""Easy tasks: one pass over the input, nothing beyond a dictionary."""

import random
import string

from app.seed.code_bank import CodeTask, pack

WORDS = ("disk", "retry", "ERROR", "user", "cache", "WARN", "timeout", "INFO", "sync", "queue")


def _log_levels(rng: random.Random, count: int) -> str:
    rows = []
    for _ in range(count):
        level = rng.choice(("ERROR", "WARN", "INFO", "DEBUG", "TRACE"))
        text = " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 4)))
        rows.append(
            f"{rng.randint(0, 23):02}:{rng.randint(0, 59):02}:{rng.randint(0, 59):02} {level} {text}"
        )
    return pack(rows)


LOG_LEVELS = CodeTask(
    key="log-levels",
    title="Сводка по уровням журнала",
    difficulty="easy",
    specializations=("devops", "backend", "qa"),
    topic="logs",
    statement=(
        "В первой строке — число записей журнала N (1 ≤ N ≤ 1200). Далее N строк вида "
        "«ЧЧ:ММ:СС УРОВЕНЬ сообщение». Уровень — одно слово: ERROR, WARN, INFO, DEBUG или TRACE. "
        "Сообщение состоит из одного или нескольких слов и может само содержать названия уровней.\n\n"
        "Выведите в одной строке через пробел три числа: сколько записей уровня ERROR, WARN и INFO."
    ),
    solution="""import sys

lines = sys.stdin.read().split("\\n")
counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
for line in lines[1 : int(lines[0]) + 1]:
    level = line.split()[1]
    if level in counts:
        counts[level] += 1
print(counts["ERROR"], counts["WARN"], counts["INFO"])
""",
    sample=pack(
        [
            "10:00:01 INFO sync started",
            "10:00:02 DEBUG queue ERROR ignored",
            "10:00:05 ERROR disk timeout",
            "10:00:09 WARN retry",
            "10:00:11 INFO sync done",
        ]
    ),
    hidden=lambda rng: [
        pack(["00:00:00 DEBUG ERROR WARN INFO", "00:00:01 TRACE INFO"]),
        _log_levels(rng, 40),
        _log_levels(rng, 400),
        _log_levels(rng, 1200),
    ],
)


def _semver(rng: random.Random, count: int, top: int) -> str:
    return pack(
        f"{rng.randint(0, top)}.{rng.randint(0, top)}.{rng.randint(0, top)} "
        f"{rng.choice(('major', 'minor', 'patch'))}"
        for _ in range(count)
    )


SEMVER_BUMP = CodeTask(
    key="semver-bump",
    title="Следующая версия",
    difficulty="easy",
    specializations=("devops", "mobile", "fullstack"),
    topic="strings",
    statement=(
        "Версии записываются как MAJOR.MINOR.PATCH — три целых числа от 0 до 999 без ведущих нулей. "
        "Изменение типа patch увеличивает третье число; minor увеличивает второе и обнуляет третье; "
        "major увеличивает первое и обнуляет остальные.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 60). В каждой из следующих T строк — текущая "
        "версия и через пробел тип изменения: major, minor или patch. Для каждого теста выведите "
        "новую версию на отдельной строке."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for i in range(int(data[0])):
    major, minor, patch = map(int, data[1 + 2 * i].split("."))
    kind = data[2 + 2 * i]
    if kind == "major":
        major, minor, patch = major + 1, 0, 0
    elif kind == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    print(f"{major}.{minor}.{patch}")
""",
    sample=pack(["1.4.2 patch", "1.4.2 minor", "1.4.2 major", "0.0.0 patch"]),
    hidden=lambda rng: [
        pack(["0.0.0 major", "0.0.0 minor", "9.9.9 patch", "9.99.999 minor", "99.0.7 major"]),
        _semver(rng, 30, 9),
        _semver(rng, 60, 99),
        _semver(rng, 60, 999),
    ],
)


def _ipv4(rng: random.Random, count: int) -> str:
    rows = []
    for _ in range(count):
        parts = [
            str(rng.choice((0, 1, 9, 10, 99, 127, 192, 255, rng.randint(0, 255)))) for _ in range(4)
        ]
        kind = rng.randint(0, 9)
        slot = rng.randrange(4)
        if kind == 0:
            parts[slot] = str(rng.randint(256, 999))
        elif kind == 1:
            parts[slot] = "0" + parts[slot]
        elif kind == 2:
            parts[slot] = ""
        elif kind == 3:
            parts.append(str(rng.randint(0, 255)))
        elif kind == 4:
            parts.pop()
        elif kind == 5:
            parts[slot] = rng.choice(("a", "1a", "-1", "x7", "+5"))
        rows.append(".".join(parts))
    return pack(rows)


IPV4_VALID = CodeTask(
    key="ipv4-valid",
    title="Проверка IPv4-адреса",
    difficulty="easy",
    specializations=("security", "devops", "backend"),
    topic="strings",
    statement=(
        "Строка считается корректным IPv4-адресом, если она состоит ровно из четырёх частей, "
        "разделённых точками, каждая часть — непустая запись целого числа от 0 до 255 из одних цифр "
        "и без ведущих нулей (сам «0» допустим).\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 180). В каждой из следующих T строк — непустая "
        "строка без пробелов длиной до 30 символов из цифр, латинских букв, точек и знаков «+» и «-». "
        "Для каждой выведите YES, если это корректный адрес, иначе NO."
    ),
    solution="""import sys


def valid(text):
    parts = text.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part or not all("0" <= ch <= "9" for ch in part):
            return False
        if len(part) > 1 and part[0] == "0":
            return False
        if int(part) > 255:
            return False
    return True


data = sys.stdin.read().split()
for text in data[1 : int(data[0]) + 1]:
    print("YES" if valid(text) else "NO")
""",
    sample=pack(["192.168.0.1", "256.1.1.1", "10.0.01.5", "1.2.3", "0.0.0.0"]),
    hidden=lambda rng: [
        pack(
            [
                "255.255.255.255",
                "1..2.3",
                "1.2.3.",
                ".1.2.3",
                "1.2.3.4.5",
                "00.0.0.0",
                "1.2.3.-4",
                "1.2.3.4a",
                "1234.1.1.1",
                "....",
                "1.2.3.+4",
                "0.10.100.249",
                "1.2.3.000000000000000000001",
            ]
        ),
        _ipv4(rng, 60),
        _ipv4(rng, 120),
        _ipv4(rng, 180),
    ],
)


def _token(rng: random.Random, low: int, high: int) -> str:
    return "".join(
        rng.choice(string.ascii_letters + string.digits) for _ in range(rng.randint(low, high))
    )


MASK_SECRET = CodeTask(
    key="mask-secret",
    title="Маскирование секрета",
    difficulty="easy",
    specializations=("security", "qa", "fullstack"),
    topic="strings",
    statement=(
        "Перед записью в журнал секрет маскируют: все символы, кроме последних четырёх, заменяют "
        "на «*». Если в секрете четыре символа или меньше, заменяют все символы.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 25). В каждой из следующих T строк — секрет: "
        "строка из латинских букв и цифр длиной от 1 до 30. Для каждого выведите его "
        "замаскированную запись."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for secret in data[1 : int(data[0]) + 1]:
    if len(secret) <= 4:
        print("*" * len(secret))
    else:
        print("*" * (len(secret) - 4) + secret[-4:])
""",
    sample=pack(["4276550012349876", "abc", "token5", "A1b2"]),
    hidden=lambda rng: [
        pack(["a", "ab", "abcd", "abcde", "x" * 30]),
        pack(_token(rng, 1, 8) for _ in range(25)),
        pack(_token(rng, 3, 30) for _ in range(25)),
        pack(_token(rng, 26, 30) for _ in range(25)),
    ],
)


def _caesar(rng: random.Random, count: int, top: int) -> str:
    return pack(
        f"{rng.randint(0, top)} {''.join(rng.choice(string.ascii_letters) for _ in range(rng.randint(1, 30)))}"
        for _ in range(count)
    )


CAESAR_SHIFT = CodeTask(
    key="caesar-shift",
    title="Расшифровка сдвигом",
    difficulty="easy",
    specializations=("security", "fullstack"),
    topic="strings",
    statement=(
        "Сообщение зашифровано шифром Цезаря: каждая латинская буква заменена буквой, стоящей в "
        "алфавите на K позиций правее, по кругу (после z идёт a, после Z — A). Регистр букв "
        "сохраняется.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 25). В каждой из следующих T строк — сдвиг K "
        "(0 ≤ K ≤ 10^9) и через пробел шифртекст из латинских букв длиной от 1 до 30. Для каждого "
        "теста выведите исходное сообщение."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for i in range(int(data[0])):
    shift = int(data[1 + 2 * i]) % 26
    plain = []
    for ch in data[2 + 2 * i]:
        base = ord("a") if ch.islower() else ord("A")
        plain.append(chr((ord(ch) - base - shift) % 26 + base))
    print("".join(plain))
""",
    sample=pack(["3 Khoor", "0 abc", "1 aAzZ", "27 bcd"]),
    hidden=lambda rng: [
        pack(["26 Same", "25 abc", "1000000000 zzzAAA", "52 x", "13 NoPqRs"]),
        _caesar(rng, 25, 25),
        _caesar(rng, 25, 1000),
        _caesar(rng, 25, 10**9),
    ],
)


def _fail_streak(rng: random.Random, count: int, users: int, fail: float) -> str:
    return pack(
        f"u{rng.randint(1, users)} {'FAIL' if rng.random() < fail else 'OK'}" for _ in range(count)
    )


FAIL_STREAK = CodeTask(
    key="fail-streak",
    title="Блокировка после неудачных входов",
    difficulty="easy",
    specializations=("security", "devops"),
    topic="logs",
    statement=(
        "В первой строке — число попыток входа N (1 ≤ N ≤ 3000). Далее N строк в порядке времени: "
        "логин пользователя (латинские буквы и цифры, до 8 символов) и через пробел результат — "
        "OK или FAIL.\n\n"
        "Учётная запись блокируется, когда у пользователя набирается три неудачные попытки подряд; "
        "успешный вход обнуляет счётчик. Выведите, сколько разных учётных записей было "
        "заблокировано хотя бы один раз."
    ),
    solution="""import sys

data = sys.stdin.read().split()
streak = {}
locked = set()
for i in range(int(data[0])):
    user, result = data[1 + 2 * i], data[2 + 2 * i]
    if result == "OK":
        streak[user] = 0
    else:
        streak[user] = streak.get(user, 0) + 1
        if streak[user] == 3:
            locked.add(user)
print(len(locked))
""",
    sample=pack(
        ["anna FAIL", "ivan FAIL", "anna FAIL", "ivan OK", "anna FAIL", "ivan FAIL", "ivan FAIL"]
    ),
    hidden=lambda rng: [
        pack(
            ["a FAIL", "a FAIL", "a OK", "a FAIL", "a FAIL", "b FAIL", "a FAIL", "a FAIL", "a FAIL"]
        ),
        _fail_streak(rng, 60, 5, 0.6),
        _fail_streak(rng, 800, 60, 0.55),
        _fail_streak(rng, 3000, 400, 0.7),
    ],
)


def _ranges(rng: random.Random, count: int, top: int, width: int) -> str:
    rows = []
    for _ in range(count):
        low = rng.randint(-top, top)
        rows.append(f"{low} {low + rng.randint(0, width)}")
    return pack(rows)


BOUNDARY_VALUES = CodeTask(
    key="boundary-values",
    title="Граничные значения",
    difficulty="easy",
    specializations=("qa",),
    topic="algorithms",
    statement=(
        "Поле принимает целые числа от A до B включительно. По технике граничных значений его "
        "проверяют на шести числах: A−1, A, A+1, B−1, B, B+1. Если диапазон узкий, часть этих чисел "
        "совпадает — повторять проверку не нужно.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 12). В каждой из следующих T строк — два целых "
        "числа A и B (−10^9 ≤ A ≤ B ≤ 10^9). Для каждого теста выведите в одной строке через пробел "
        "все различные проверочные числа по возрастанию."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for i in range(int(data[0])):
    a, b = int(data[1 + 2 * i]), int(data[2 + 2 * i])
    print(*sorted({a - 1, a, a + 1, b - 1, b, b + 1}))
""",
    sample=pack(["1 100", "5 5", "0 1", "-3 -1"]),
    hidden=lambda rng: [
        pack(["0 0", "0 2", "0 3", "-1 0", "-1000000000 1000000000", "7 8"]),
        _ranges(rng, 12, 20, 3),
        _ranges(rng, 12, 1000, 1000),
        _ranges(rng, 12, 10**9 - 5, 4),
    ],
)


def _mismatch(rng: random.Random, count: int, broken: float) -> str:
    expected, actual = [], []
    for _ in range(count):
        line = " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 4)))
        expected.append(line + " " * rng.choice((0, 0, 1, 3)))
        roll = rng.random()
        if roll < broken:
            actual.append(
                rng.choice(
                    (line + " x", line.lower() + "!", " " + line, line.replace(" ", "  ") + "?")
                )
            )
        else:
            actual.append(line + " " * rng.choice((0, 0, 2)))
    return f"{count}\n" + "\n".join(expected + actual) + "\n"


FIRST_MISMATCH = CodeTask(
    key="first-mismatch",
    title="Сравнение вывода с эталоном",
    difficulty="easy",
    specializations=("qa", "devops"),
    topic="strings",
    statement=(
        "В первой строке — число N (1 ≤ N ≤ 500). В следующих N строках — ожидаемый вывод программы, "
        "ещё в N строках — фактический. Строки состоят из латинских букв, цифр, пробелов и знаков "
        "препинания, длина каждой не больше 40.\n\n"
        "Строки с одинаковым номером считаются совпавшими, если они равны после удаления пробелов в "
        "конце строки; пробелы в начале и внутри значимы. Выведите через пробел два числа: сколько "
        "строк не совпало и номер первой несовпавшей строки (нумерация с 1). Если совпали все, "
        "выведите «0 0»."
    ),
    solution="""import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
lines += [""] * (2 * n + 1 - len(lines))
count = first = 0
for i in range(n):
    if lines[1 + i].rstrip(" ") != lines[1 + n + i].rstrip(" "):
        count += 1
        if first == 0:
            first = i + 1
print(count, first)
""",
    sample="3\nready\ntotal 5\ndone\nready  \ntotal 6\n done\n",
    hidden=lambda rng: [
        "2\nok\nsum 10   \nok \nsum 10\n",
        _mismatch(rng, 30, 0.2),
        _mismatch(rng, 200, 0.05),
        _mismatch(rng, 500, 0.5),
    ],
)


def _records(rng: random.Random, count: int, ids: int) -> str:
    stamps = rng.sample(range(1, 10**9), count)
    return pack(f"{rng.randint(1, ids)} {stamp} {rng.randint(-(10**6), 10**6)}" for stamp in stamps)


LATEST_RECORDS = CodeTask(
    key="latest-records",
    title="Актуальные версии записей",
    difficulty="easy",
    specializations=("data-engineering", "backend", "data-science"),
    topic="data",
    statement=(
        "В таблицу изменений попадают версии записей в произвольном порядке. В первой строке — "
        "число версий N (1 ≤ N ≤ 2500). В каждой из следующих N строк — три целых числа: "
        "идентификатор записи (от 1 до 10^9), время изменения (от 1 до 10^9, все времена различны) "
        "и значение (от −10^6 до 10^6).\n\n"
        "Для каждой записи актуальна версия с наибольшим временем изменения. Выведите через пробел "
        "число различных записей и сумму значений их актуальных версий."
    ),
    solution="""import sys

data = sys.stdin.read().split()
latest = {}
for i in range(int(data[0])):
    key, stamp, value = int(data[1 + 3 * i]), int(data[2 + 3 * i]), int(data[3 + 3 * i])
    if key not in latest or latest[key][0] < stamp:
        latest[key] = (stamp, value)
print(len(latest), sum(value for _, value in latest.values()))
""",
    sample=pack(["7 100 50", "3 20 -5", "7 90 10", "3 25 8", "9 1 0"]),
    hidden=lambda rng: [
        pack(["1 5 10", "1 4 99", "1 6 -3", "1 1 7"]),
        _records(rng, 50, 8),
        _records(rng, 600, 10**9),
        _records(rng, 2500, 300),
    ],
)


def _series(rng: random.Random, cases: int, size: int, gaps: float) -> str:
    rows = []
    for _ in range(cases):
        n = rng.randint(1, size)
        rows.append(str(n))
        rows.append(
            " ".join(
                "NA" if rng.random() < gaps else str(rng.randint(-1000, 1000)) for _ in range(n)
            )
        )
    return f"{cases}\n" + "\n".join(rows) + "\n"


FORWARD_FILL = CodeTask(
    key="forward-fill",
    title="Заполнение пропусков",
    difficulty="easy",
    specializations=("data-engineering", "data-science"),
    topic="data",
    statement=(
        "В ряде измерений часть значений пропущена и записана как NA. Пропуск заполняют последним "
        "известным значением слева от него. Пропуски в начале ряда, слева от которых значений нет, "
        "заполняют первым известным значением. Если известных значений нет совсем, все пропуски "
        "считаются нулями.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 100). Каждый тест занимает две строки: длина "
        "ряда n (1 ≤ n ≤ 500) и n элементов через пробел — целые числа от −1000 до 1000 или NA. "
        "Для каждого теста выведите сумму ряда после заполнения."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n = int(data[pos])
    row = data[pos + 1 : pos + 1 + n]
    pos += 1 + n
    last = next((int(item) for item in row if item != "NA"), 0)
    total = 0
    for item in row:
        if item != "NA":
            last = int(item)
        total += last
    print(total)
""",
    sample="4\n5\n3 NA NA 7 NA\n3\nNA NA 4\n2\nNA NA\n1\n-6\n",
    hidden=lambda rng: [
        "5\n1\nNA\n4\nNA 5 NA NA\n3\n-2 NA 2\n3\nNA NA -1\n4\n0 NA NA NA\n",
        _series(rng, 40, 8, 0.5),
        _series(rng, 100, 60, 0.3),
        _series(rng, 20, 500, 0.8),
    ],
)


def _mode(rng: random.Random, cases: int, size: int, spread: int) -> str:
    rows = []
    for _ in range(cases):
        n = rng.randint(1, size)
        rows.append(str(n))
        rows.append(" ".join(str(rng.randint(-spread, spread)) for _ in range(n)))
    return f"{cases}\n" + "\n".join(rows) + "\n"


MODE_VALUE = CodeTask(
    key="mode-value",
    title="Мода выборки",
    difficulty="easy",
    specializations=("data-science", "data-engineering"),
    topic="statistics",
    statement=(
        "Мода выборки — значение, которое встречается в ней чаще остальных. Если таких значений "
        "несколько, модой считается наименьшее из них.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 60). Каждый тест занимает две строки: размер "
        "выборки n (1 ≤ n ≤ 800) и n целых чисел от −10^9 до 10^9. Для каждого теста выведите через "
        "пробел моду и число её вхождений."
    ),
    solution="""import sys

data = sys.stdin.read().split()
pos = 1
for _ in range(int(data[0])):
    n = int(data[pos])
    counts = {}
    for item in data[pos + 1 : pos + 1 + n]:
        counts[item] = counts.get(item, 0) + 1
    pos += 1 + n
    best = max(counts.values())
    print(min(int(item) for item, count in counts.items() if count == best), best)
""",
    sample="3\n6\n4 1 4 2 1 9\n1\n-7\n5\n3 3 3 3 3\n",
    hidden=lambda rng: [
        "4\n4\n-1 -2 -2 -1\n3\n10 9 8\n2\n1000000000 -1000000000\n5\n0 0 1 1 2\n",
        _mode(rng, 60, 10, 3),
        _mode(rng, 60, 200, 15),
        _mode(rng, 6, 800, 10**9),
    ],
)


def _pages(rng: random.Random, count: int, top: int) -> str:
    rows = []
    for _ in range(count):
        size = rng.randint(1, max(1, top // rng.choice((1, 3, 10, 50))))
        total = rng.randint(0, top)
        pages = -(-total // size)
        rows.append(f"{total} {size} {rng.randint(1, pages + 2)}")
    return pack(rows)


PAGE_RANGE = CodeTask(
    key="page-range",
    title="Границы страницы",
    difficulty="easy",
    specializations=("frontend", "fullstack", "mobile", "backend"),
    topic="algorithms",
    statement=(
        "Список из N элементов показывают страницами по K элементов; элементы пронумерованы с 1, "
        "последняя страница может быть неполной.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 20). В каждой из следующих T строк — три целых "
        "числа: N (0 ≤ N ≤ 10^12), K (1 ≤ K ≤ 10^12) и номер страницы P (1 ≤ P ≤ 10^12). Для каждого "
        "теста выведите через пробел три числа: номер первого элемента на странице P, номер "
        "последнего и общее число страниц. Если страницы P не существует, вместо первых двух чисел "
        "выведите нули."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for i in range(int(data[0])):
    total, size, page = (int(item) for item in data[1 + 3 * i : 4 + 3 * i])
    pages = (total + size - 1) // size
    if page > pages:
        print(0, 0, pages)
    else:
        print((page - 1) * size + 1, min(page * size, total), pages)
""",
    sample=pack(["45 10 2", "45 10 5", "45 10 6", "0 10 1"]),
    hidden=lambda rng: [
        pack(
            ["1 1 1", "10 10 1", "10 10 2", "11 10 2", "5 100 1", "1000000000000 1 1000000000000"]
        ),
        _pages(rng, 20, 30),
        _pages(rng, 20, 10**6),
        _pages(rng, 20, 10**12),
    ],
)


def _colors(rng: random.Random, count: int, short: float) -> str:
    rows = []
    for _ in range(count):
        if rng.random() < short:
            rows.append(" ".join(str(17 * rng.randint(0, 15)) for _ in range(3)))
        else:
            rows.append(" ".join(str(rng.randint(0, 255)) for _ in range(3)))
    return pack(rows)


RGB_HEX = CodeTask(
    key="rgb-hex",
    title="Цвет в шестнадцатеричной записи",
    difficulty="easy",
    specializations=("frontend", "mobile", "gamedev"),
    topic="strings",
    statement=(
        "Цвет задан тремя компонентами R, G, B — целыми числами от 0 до 255. Его записывают как "
        "#RRGGBB: каждая компонента — двумя шестнадцатеричными цифрами в верхнем регистре. Если у "
        "каждой из трёх компонент обе цифры одинаковы, используют короткую запись #RGB.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 100). В каждой из следующих T строк — три числа "
        "R, G, B. Для каждого теста выведите запись цвета, короткую — когда она возможна."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for i in range(int(data[0])):
    code = "".join(f"{int(item):02X}" for item in data[1 + 3 * i : 4 + 3 * i])
    if code[0] == code[1] and code[2] == code[3] and code[4] == code[5]:
        code = code[0] + code[2] + code[4]
    print("#" + code)
""",
    sample=pack(["255 136 0", "64 47 255", "0 0 0", "10 11 12"]),
    hidden=lambda rng: [
        pack(["255 255 255", "17 34 51", "17 34 50", "1 1 1", "170 187 204", "16 0 0"]),
        _colors(rng, 60, 0.5),
        _colors(rng, 100, 0.2),
        _colors(rng, 100, 0.9),
    ],
)


def _walks(rng: random.Random, cases: int, side: int, length: int) -> str:
    rows = []
    for _ in range(cases):
        rows.append(f"{rng.randint(1, side)} {rng.randint(1, side)}")
        rows.append("".join(rng.choice("UDLR") for _ in range(rng.randint(1, length))))
    return f"{cases}\n" + "\n".join(rows) + "\n"


GRID_WALK = CodeTask(
    key="grid-walk",
    title="Персонаж на поле",
    difficulty="easy",
    specializations=("gamedev", "mobile", "frontend"),
    topic="algorithms",
    statement=(
        "Поле состоит из W столбцов и H строк. Персонаж стоит в левой верхней клетке с "
        "координатами (0, 0); x растёт вправо, y — вниз. Команды: L — на клетку влево, R — вправо, "
        "U — вверх, D — вниз. Команда, которая вывела бы персонажа за границу поля, игнорируется.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 50). Каждый тест занимает две строки: числа W и H "
        "(1 ≤ W, H ≤ 10^9) и строка команд длиной от 1 до 1000. Для каждого теста выведите через "
        "пробел координаты x и y персонажа после выполнения всех команд."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for i in range(int(data[0])):
    width, height = int(data[1 + 3 * i]), int(data[2 + 3 * i])
    x = y = 0
    for command in data[3 + 3 * i]:
        if command == "L":
            x = max(x - 1, 0)
        elif command == "R":
            x = min(x + 1, width - 1)
        elif command == "U":
            y = max(y - 1, 0)
        else:
            y = min(y + 1, height - 1)
    print(x, y)
""",
    sample="3\n3 2\nRRRRDDL\n5 5\nULUL\n1 1\nRDLU\n",
    hidden=lambda rng: [
        "4\n1 5\nRRDDDDDDU\n5 1\nDDRRRRRRL\n2 2\nRDLURDLU\n1000000000 1000000000\nRRDD\n",
        _walks(rng, 50, 4, 30),
        _walks(rng, 50, 40, 1000),
        _walks(rng, 50, 10**9, 1000),
    ],
)


def _rects(rng: random.Random, count: int, top: int) -> str:
    rows = []
    for _ in range(count):
        coords = []
        for _ in range(2):
            x1, x2 = rng.sample(range(-top, top + 1), 2)
            y1, y2 = rng.sample(range(-top, top + 1), 2)
            coords += [x1, y1, x2, y2]
        rows.append(" ".join(map(str, coords)))
    return pack(rows)


RECT_OVERLAP = CodeTask(
    key="rect-overlap",
    title="Пересечение хитбоксов",
    difficulty="easy",
    specializations=("gamedev", "mobile"),
    topic="algorithms",
    statement=(
        "Хитбокс — прямоугольник со сторонами, параллельными осям координат. Он задаётся "
        "координатами двух противоположных углов; углы могут быть перечислены в любом порядке.\n\n"
        "В первой строке — число тестов T (1 ≤ T ≤ 40). В каждой из следующих T строк — восемь "
        "целых чисел от −10^9 до 10^9: x1 y1 x2 y2 для первого прямоугольника и x3 y3 x4 y4 для "
        "второго. Площадь каждого прямоугольника положительна. Для каждого теста выведите площадь "
        "общей части прямоугольников; если они не пересекаются или только касаются, выведите 0."
    ),
    solution="""import sys

data = sys.stdin.read().split()
for i in range(int(data[0])):
    x1, y1, x2, y2, x3, y3, x4, y4 = (int(item) for item in data[1 + 8 * i : 9 + 8 * i])
    width = min(max(x1, x2), max(x3, x4)) - max(min(x1, x2), min(x3, x4))
    height = min(max(y1, y2), max(y3, y4)) - max(min(y1, y2), min(y3, y4))
    print(width * height if width > 0 and height > 0 else 0)
""",
    sample=pack(["0 0 4 4 2 2 6 6", "4 4 0 0 6 2 2 6", "0 0 1 1 1 0 2 1", "0 0 10 10 3 3 4 5"]),
    hidden=lambda rng: [
        pack(
            [
                "0 0 2 2 2 2 4 4",
                "0 0 2 2 3 3 5 5",
                "-5 -5 5 5 5 5 -5 -5",
                "0 5 5 0 1 -1 2 9",
                "-1000000000 -1000000000 1000000000 1000000000 1000000000 1000000000 -1000000000 -1000000000",
                "0 0 3 3 -1 1 4 2",
            ]
        ),
        _rects(rng, 40, 5),
        _rects(rng, 40, 100),
        _rects(rng, 40, 10**9),
    ],
)


TASKS = [
    LOG_LEVELS,
    SEMVER_BUMP,
    IPV4_VALID,
    MASK_SECRET,
    CAESAR_SHIFT,
    FAIL_STREAK,
    BOUNDARY_VALUES,
    FIRST_MISMATCH,
    LATEST_RECORDS,
    FORWARD_FILL,
    MODE_VALUE,
    PAGE_RANGE,
    RGB_HEX,
    GRID_WALK,
    RECT_OVERLAP,
]
