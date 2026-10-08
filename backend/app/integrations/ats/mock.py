"""In-process ATS for local development and the demo. No network."""

from app.integrations.ats.normalized import (
    AtsRecord,
    NormalizedApplication,
    NormalizedCandidate,
    NormalizedJob,
    PollChange,
    PollPage,
)

_JOB = NormalizedJob(
    external_id="mock-job-1",
    title="Бэкенд-разработчик",
    required_skills=("Python", "PostgreSQL"),
    salary_from=200_000,
    salary_to=320_000,
    city="Москва",
)


def _application(
    external_id: str,
    *,
    name: str,
    skills: tuple[str, ...],
    city: str,
    salary: int,
    years: int,
) -> NormalizedApplication:
    return NormalizedApplication(
        external_id=external_id,
        candidate=NormalizedCandidate(
            external_id=f"{external_id}-person",
            name=name,
            skills=skills,
            experience_years=years,
            city=city,
            salary_expectation=salary,
            resume_text=f"{name}: {', '.join(skills)}",
        ),
        job=_JOB,
    )


_ITEMS: tuple[PollChange, ...] = (
    PollChange(
        external_event_id="mock-evt-1",
        raw={"source": "mock", "event": "mock-evt-1"},
        application=_application(
            "mock-app-1",
            name="Мария Соколова",
            skills=("Python", "PostgreSQL", "FastAPI"),
            city="Москва",
            salary=250_000,
            years=5,
        ),
    ),
    PollChange(
        external_event_id="mock-evt-2",
        raw={"source": "mock", "event": "mock-evt-2"},
        application=_application(
            "mock-app-2",
            name="Илья Орлов",
            skills=("Figma", "Photoshop"),
            city="Санкт-Петербург",
            salary=400_000,
            years=3,
        ),
    ),
    PollChange(
        external_event_id="mock-evt-3",
        raw={"source": "mock", "event": "mock-evt-3"},
        application=_application(
            "mock-app-3",
            name="Кирилл Панков",
            skills=("Python",),
            city="Москва",
            salary=300_000,
            years=2,
        ),
    ),
)


class MockAtsProvider:
    """Three fixed applications. The cursor is how many of them a poll has already walked past."""

    name = "mock"

    def __init__(self) -> None:
        self._written: dict[str, list[AtsRecord]] = {}

    async def poll(self, cursor: str | None) -> PollPage:
        start = _cursor_index(cursor)
        batch = _ITEMS[start:]
        return PollPage(changes=batch, next_cursor=str(len(_ITEMS)))

    async def write_tag(self, external_application_id: str, tag: str) -> None:
        self._remember(external_application_id, AtsRecord(kind="tag", value=tag))

    async def write_note(self, external_application_id: str, note: str) -> None:
        self._remember(external_application_id, AtsRecord(kind="note", value=note))

    async def write_score(self, external_application_id: str, score: int) -> None:
        self._remember(external_application_id, AtsRecord(kind="score", value=str(score)))

    def records(self, external_application_id: str) -> tuple[AtsRecord, ...]:
        return tuple(self._written.get(external_application_id, ()))

    def _remember(self, external_application_id: str, record: AtsRecord) -> None:
        self._written.setdefault(external_application_id, []).append(record)


def _cursor_index(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        index = int(cursor)
    except ValueError:
        return 0
    return max(0, min(index, len(_ITEMS)))
