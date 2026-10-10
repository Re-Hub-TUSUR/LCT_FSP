"""A candidate's resume as a PDF: what the profile page shows, laid out for print and mail.

Fonts are the site's own (`app/assets/fonts`, copied from the frontend): TDAText for the name,
JetBrains Mono for the text. The document is built from `CandidateRead`, so it shows exactly what
the viewer may see on the site: contacts only to the candidate and to an employer they accepted.
"""

import hashlib
import io
import logging
import tempfile
import uuid
from collections.abc import Sequence
from datetime import datetime
from functools import cache, lru_cache
from pathlib import Path
from typing import Final

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fpdf import FPDF, XPos, YPos
from PIL import Image

from app.models.enums import FspEventLevel, FspOutcome, FspParticipation, JobStatus
from app.schemas.candidate import CandidateRead, ExperienceEntry, FspAchievementRead
from app.services.categories import (
    EMPLOYMENT_LABELS,
    FSP_DISCIPLINE_LABELS,
    FSP_EVENT_KIND_LABELS,
    FSP_OUTCOME_LABELS,
    FSP_TITLE_LABELS,
    SPECIALIZATIONS,
    WORK_FORMAT_LABELS,
)
from app.services.matching import rub
from app.services.uploads import MAX_IMAGE_PIXELS

logger = logging.getLogger(__name__)

FONTS: Final = Path(__file__).resolve().parent.parent / "assets" / "fonts"
TEXT_FONT: Final = FONTS / "JetBrainsMono-Variable.ttf"
NAME_FONT: Final = FONTS / "TDAText.ttf"
MONO: Final = "JetBrainsMono"
ACCENT: Final = "TDAText"

INK: Final = (27, 28, 33)
MUTED: Final = (110, 111, 117)
BLUE: Final = (64, 47, 255)
LINE: Final = (214, 215, 222)

REGULAR: Final = 400
BOLD: Final = 700

MARGIN: Final = 18.0
PHOTO: Final = 30.0
LABEL_WIDTH: Final = 42.0
MONTHS_IN_YEAR: Final = 12
# A section heading this close to the bottom moves to the next page with its text.
KEEP_WITH_NEXT: Final = 28.0

MONTHS: Final = (
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь",
)
# Third person: the resume is read by somebody else.
JOB_STATUS_LABELS: Final = {
    JobStatus.ACTIVE: "активно ищет работу",
    JobStatus.OPEN: "рассматривает предложения",
    JobStatus.NOT_LOOKING: "не ищет работу",
}
LEVEL_LABELS: Final = {
    FspEventLevel.REGIONAL: "региональный уровень",
    FspEventLevel.NATIONAL: "всероссийский уровень",
    FspEventLevel.INTERNATIONAL: "международный уровень",
}


def plural(count: int, forms: tuple[str, str, str]) -> str:
    tens, units = count % 100, count % 10
    if 11 <= tens <= 14:  # noqa: PLR2004 - Russian plural rules
        return forms[2]
    if units == 1:
        return forms[0]
    if 2 <= units <= 4:  # noqa: PLR2004 - Russian plural rules
        return forms[1]
    return forms[2]


def years(count: int) -> str:
    return f"{count} {plural(count, ('год', 'года', 'лет'))}"


def _month(value: str) -> str:
    year, month = value.split("-")
    return f"{MONTHS[int(month) - 1]} {year}"


def _months_between(start: str, end: str) -> int:
    start_year, start_month = (int(part) for part in start.split("-"))
    end_year, end_month = (int(part) for part in end.split("-"))
    return (end_year - start_year) * MONTHS_IN_YEAR + end_month - start_month + 1


def period(entry: ExperienceEntry, *, now: datetime) -> str:
    """«январь 2022 — по настоящее время · 2 года 9 месяцев»."""
    end = entry.end or f"{now.year:04d}-{now.month:02d}"
    span = max(_months_between(entry.start, end), 1)
    full_years, months = divmod(span, MONTHS_IN_YEAR)
    length = " ".join(
        part
        for part in (
            years(full_years) if full_years else "",
            f"{months} {plural(months, ('месяц', 'месяца', 'месяцев'))}" if months else "",
        )
        if part
    )
    finish = _month(entry.end) if entry.end else "по настоящее время"
    return f"{_month(entry.start)} — {finish} · {length}"


def fsp_line(item: FspAchievementRead) -> str:
    """«Призёр, 2-е место · Кубок России · алгоритмическое программирование, 2025»."""
    outcome = FSP_OUTCOME_LABELS[item.result].capitalize()
    if item.place is not None and item.result != FspOutcome.WINNER:
        outcome += f", {item.place}-е место"
    parts = [
        outcome,
        item.event_name,
        f"{FSP_DISCIPLINE_LABELS[item.discipline]}, {item.year}",
        f"{FSP_EVENT_KIND_LABELS[item.event_kind]}, {LEVEL_LABELS[item.level]}",
    ]
    if item.participation == FspParticipation.TEAM:
        parts.append(f"команда «{item.team_name}»" if item.team_name else "командный зачёт")
    return " · ".join(parts)


@cache
def static_font(weight: int) -> Path:
    """JetBrains Mono at one weight. Instancing the variable font takes a third of a second, so
    it happens once per process; the file is named by the source's hash."""
    digest = hashlib.sha256(TEXT_FONT.read_bytes()).hexdigest()[:12]
    target = Path(tempfile.gettempdir()) / "kadry-fonts" / f"JetBrainsMono-{weight}-{digest}.ttf"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        font = instancer.instantiateVariableFont(TTFont(TEXT_FONT), {"wght": weight})
        partial = target.with_suffix(f".{uuid.uuid4().hex}.tmp")
        font.save(partial)
        partial.replace(target)
    return target


@lru_cache(maxsize=1)
def _printable_codes() -> frozenset[int]:
    return frozenset(TTFont(TEXT_FONT).getBestCmap())


def printable(text: str) -> str:
    """The text without the characters the font cannot draw (emoji and the like)."""
    codes = _printable_codes()
    return "".join(char for char in text if char in "\n\t" or ord(char) in codes)


class _Resume(FPDF):
    def __init__(self, footer: str) -> None:
        super().__init__(format="A4")
        self._footer = footer
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.set_auto_page_break(auto=True, margin=22)
        self.add_font(MONO, "", static_font(REGULAR))
        self.add_font(MONO, "B", static_font(BOLD))
        self.add_font(ACCENT, "", NAME_FONT)
        # A letter missing in TDAText is drawn in JetBrains Mono.
        self.set_fallback_fonts([MONO])

    @property
    def width(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font(MONO, size=7)
        self.set_text_color(*MUTED)
        self.cell(0, 5, self._footer, align="L")
        self.set_x(self.l_margin)
        self.cell(0, 5, f"{self.page_no()} / {{nb}}", align="R")

    def text_block(
        self, text: str, *, size: float = 9.5, bold: bool = False, color: tuple[int, ...] = INK
    ) -> None:
        self.set_font(MONO, "B" if bold else "", size)
        self.set_text_color(*color)
        self.multi_cell(
            0, size * 0.5, printable(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L"
        )

    def section(self, title: str) -> None:
        if self.get_y() > self.h - self.b_margin - KEEP_WITH_NEXT:
            self.add_page()
        self.ln(5)
        self.set_font(MONO, "B", 8)
        self.set_text_color(*BLUE)
        self.set_char_spacing(1.2)
        self.cell(0, 5, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        self.set_char_spacing(0)
        y = self.get_y() + 0.8
        self.set_draw_color(*LINE)
        self.set_line_width(0.3)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(3.5)

    def fact(self, label: str, value: str) -> None:
        self.set_font(MONO, "", 8)
        self.set_text_color(*MUTED)
        top = self.get_y()
        self.cell(LABEL_WIDTH, 5, label)
        self.set_xy(self.l_margin + LABEL_WIDTH, top)
        self.set_font(MONO, "", 9.5)
        self.set_text_color(*INK)
        self.multi_cell(0, 5, printable(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        self.ln(0.6)


def _photo(pdf: _Resume, data: bytes) -> bool:
    """The photo in the top right corner; a broken file is left out."""
    try:
        image = Image.open(io.BytesIO(data))
        # The header is read, the pixels are not yet: a photo saved before uploads checked the
        # size must not unpack into gigabytes here.
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise ValueError("the photo is too large")
        image.load()
    except (OSError, ValueError, Image.DecompressionBombError):
        logger.warning("The profile photo could not be read; the resume goes without it")
        return False
    side = min(image.size)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    square = image.convert("RGB").crop((left, top, left + side, top + side))
    pdf.image(square, x=pdf.w - pdf.r_margin - PHOTO, y=MARGIN, w=PHOTO, h=PHOTO)
    return True


def _header(pdf: _Resume, candidate: CandidateRead, photo: bytes | None) -> None:
    has_photo = photo is not None and _photo(pdf, photo)
    width = pdf.width - (PHOTO + 6 if has_photo else 0)

    pdf.set_font(MONO, "B", 7.5)
    pdf.set_text_color(*BLUE)
    pdf.set_char_spacing(1.5)
    pdf.cell(width, 5, "РЕЗЮМЕ · КАДРЫ", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.set_char_spacing(0)
    pdf.ln(1.5)

    pdf.set_font(ACCENT, size=22)
    pdf.set_text_color(*INK)
    pdf.multi_cell(width, 9, candidate.display_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    if candidate.headline:
        pdf.ln(1)
        pdf.set_font(MONO, "", 11)
        pdf.multi_cell(
            width,
            5.5,
            printable(candidate.headline),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="L",
        )
    pdf.ln(2)
    category = candidate.category.label if candidate.category else None
    proof = (
        f"грейд подтверждён тестом: {candidate.assessment_score:.0f} из 100"
        if candidate.assessment_score is not None
        else "грейд указан без теста"
    )
    pdf.set_font(MONO, "B", 9)
    pdf.set_text_color(*BLUE)
    pdf.multi_cell(
        width,
        4.8,
        " · ".join(part for part in (category, proof) if part),
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="L",
    )
    # Below the photo whatever the length of the text next to it.
    if has_photo:
        pdf.set_y(max(pdf.get_y(), MARGIN + PHOTO))


def _facts(pdf: _Resume, candidate: CandidateRead) -> None:
    pdf.section("Основное")
    pdf.fact("Готовность", JOB_STATUS_LABELS[candidate.job_status])
    if candidate.city:
        place = candidate.city + (", готовность к переезду" if candidate.relocation_ready else "")
        pdf.fact("Город", place)
    if candidate.work_formats:
        pdf.fact(
            "Формат", ", ".join(WORK_FORMAT_LABELS[fmt].lower() for fmt in candidate.work_formats)
        )
    if candidate.employment_types:
        pdf.fact(
            "Занятость", ", ".join(EMPLOYMENT_LABELS[kind] for kind in candidate.employment_types)
        )
    if candidate.salary_expectation:
        pdf.fact("Ожидания", f"от {rub(candidate.salary_expectation)} на руки в месяц")
    if candidate.no_experience:
        pdf.fact("Опыт", "без коммерческого опыта")
    elif candidate.experience_years is not None:
        pdf.fact("Опыт", years(candidate.experience_years))
    if candidate.english_level:
        pdf.fact("Английский", candidate.english_level)
    if candidate.is_minor:
        pdf.fact("Возраст", "до 18 лет")


def _contacts(pdf: _Resume, candidate: CandidateRead) -> None:
    contacts = candidate.contacts
    if contacts is None and not candidate.github_url:
        return
    pdf.section("Контакты")
    if contacts is not None:
        pdf.fact("Почта", contacts.email)
        if contacts.phone:
            pdf.fact("Телефон", contacts.phone)
        if contacts.telegram:
            pdf.fact("Telegram", contacts.telegram)
    if candidate.github_url:
        pdf.fact("GitHub", candidate.github_url)


def _skills(pdf: _Resume, candidate: CandidateRead) -> None:
    if candidate.about:
        pdf.section("О себе")
        pdf.text_block(candidate.about)
    if candidate.stack or candidate.soft_skills:
        pdf.section("Навыки")
        if candidate.stack:
            pdf.fact("Стек", ", ".join(candidate.stack))
        if candidate.soft_skills:
            pdf.fact("Soft skills", ", ".join(candidate.soft_skills))


def _experience(pdf: _Resume, entries: Sequence[ExperienceEntry], *, now: datetime) -> None:
    if not entries:
        return
    pdf.section("Опыт работы")
    for entry in sorted(
        entries, key=lambda item: (item.end or "9999-99", item.start), reverse=True
    ):
        pdf.text_block(f"{entry.position} — {entry.company}", bold=True, size=10)
        pdf.text_block(period(entry, now=now), size=8.5, color=MUTED)
        if entry.stack:
            pdf.text_block(", ".join(entry.stack), size=8.5)
        pdf.ln(2.5)


def _education(pdf: _Resume, candidate: CandidateRead) -> None:
    if not candidate.education:
        return
    pdf.section("Образование")
    for item in candidate.education:
        pdf.text_block(item.institution, bold=True, size=10)
        details = ", ".join(
            part for part in (item.specialty, str(item.year) if item.year else None) if part
        )
        if details:
            pdf.text_block(details, size=8.5, color=MUTED)
        pdf.ln(2.5)


def _fsp(pdf: _Resume, candidate: CandidateRead) -> None:
    if not candidate.fsp_achievements and not candidate.fsp_titles:
        return
    pdf.section("Федерация спортивного программирования")
    for title in candidate.fsp_titles:
        pdf.text_block(
            f"{FSP_TITLE_LABELS[title.kind]} · {FSP_DISCIPLINE_LABELS[title.discipline]}, "
            f"{title.awarded_year}",
            bold=True,
        )
        pdf.ln(1.5)
    for achievement in sorted(candidate.fsp_achievements, key=lambda item: item.year, reverse=True):
        pdf.text_block(fsp_line(achievement))
        pdf.ln(1.5)
    pdf.text_block("Результаты подтверждены реестром ФСП.", size=8, color=MUTED)


def _other_resumes(pdf: _Resume, candidate: CandidateRead) -> None:
    others = [resume for resume in candidate.resumes if not resume.is_primary]
    if not others:
        return
    pdf.section("Другие профессии")
    for resume in others:
        name = SPECIALIZATIONS.get(resume.specialization or "", resume.specialization or "")
        pdf.text_block(resume.headline or name, bold=True, size=10)
        if resume.stack:
            pdf.text_block(", ".join(resume.stack), size=8.5)
        pdf.ln(2.5)


def render_resume(candidate: CandidateRead, *, photo: bytes | None, now: datetime) -> bytes:
    """The resume as PDF bytes."""
    pdf = _Resume(
        f"Сформировано на платформе КАДРЫ (ФСП России) {now:%d.%m.%Y}",
    )
    pdf.set_title(f"Резюме — {candidate.display_name}")
    pdf.set_author(candidate.display_name)
    pdf.set_creator("КАДРЫ — платформа подбора ИТ-специалистов ФСП России")
    pdf.add_page()
    _header(pdf, candidate, photo)
    _facts(pdf, candidate)
    _contacts(pdf, candidate)
    _skills(pdf, candidate)
    _experience(pdf, candidate.experience_entries, now=now)
    _education(pdf, candidate)
    _fsp(pdf, candidate)
    _other_resumes(pdf, candidate)
    return bytes(pdf.output())
