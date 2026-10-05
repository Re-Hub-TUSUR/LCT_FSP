"""IT slang a recruiter types, mapped to the words profiles use. Shared by both search engines."""

SYNONYM_GROUPS: tuple[tuple[str, ...], ...] = (
    ("python", "питон", "пайтон"),
    ("java", "джава", "ява"),
    ("golang", "go", "го"),
    ("kotlin", "котлин"),
    ("rust", "раст"),
    ("php", "пхп"),
    ("javascript", "js", "джаваскрипт"),
    ("typescript", "ts", "тайпскрипт"),
    ("react", "реакт"),
    ("vue", "вью"),
    ("angular", "ангуляр"),
    ("node.js", "nodejs", "node", "нода"),
    ("postgresql", "postgres", "постгрес"),
    ("kafka", "кафка"),
    ("kubernetes", "k8s", "кубер", "кубернетес"),
    ("docker", "докер"),
    ("swift", "свифт"),
    ("flutter", "флаттер"),
    ("unity", "юнити"),
    ("intern", "стажер", "стажёр"),
    ("junior", "джун", "джуниор"),
    ("middle", "мидл", "миддл"),
    ("senior", "сеньор", "синьор", "сениор"),
    ("lead", "лид", "тимлид", "teamlead"),
    ("backend", "бэкенд", "бекенд", "бэк"),
    ("frontend", "фронтенд", "фронт"),
    ("fullstack", "фулстек", "фуллстек"),
    ("devops", "девопс"),
    ("qa", "тестировщик", "тестирование"),
    ("ml", "машинное"),
    ("pentest", "пентест", "пентестер"),
    ("ctf", "цтф"),
    ("ios", "айос"),
    ("android", "андроид"),
)

_ALTERNATIVES: dict[str, tuple[str, ...]] = {
    word: group for group in SYNONYM_GROUPS for word in group
}


def alternatives(token: str) -> tuple[str, ...]:
    """The token itself and its synonyms, lowercase."""
    return _ALTERNATIVES.get(token, (token,))


def elasticsearch_rules() -> list[str]:
    """`synonym_graph` rules: each group is a set of equivalent words."""
    return [", ".join(group) for group in SYNONYM_GROUPS]
