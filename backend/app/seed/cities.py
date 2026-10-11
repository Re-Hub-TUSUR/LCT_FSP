"""Load Russian populated places from GeoNames and attach them to stored cities.

`python -m app.seed.cities [--if-missing]`

Downloads `cities1000.zip` (places with at least 1 000 inhabitants) and `admin1Codes.txt`,
keeps Russia, and writes a row for every free-text city that did not match one place.
"""

import argparse
import asyncio
import difflib
import sys
import zipfile
from http.client import IncompleteRead
from io import BytesIO, TextIOWrapper
from pathlib import Path
from urllib.request import urlopen

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_engine, get_sessionmaker
from app.models.candidate import CandidateProfile
from app.models.city import City, CityAlias, CityResolutionGap
from app.models.vacancy import Vacancy
from app.repositories.city import CityRepository, normalize_city_query
from app.services.cities import bind_stored_cities

# Official dump first. The mirror is used when that host stalls after the first block.
_ALIYUN = (
    "https://mirrors.aliyun.com/android.googlesource.com.bak"
    "/external/geonames/export/dump/cities1000.zip"
)
CITIES_URLS = (
    "https://download.geonames.org/export/dump/cities1000.zip",
    _ALIYUN,
)
_ADMIN1_MIRROR = "https://raw.githubusercontent.com/edsu/geonames-localsolr/master/admin1Codes.txt"
ADMIN1_URLS = (
    "https://download.geonames.org/export/dump/admin1CodesASCII.txt",
    "http://download.geonames.org/export/dump/admin1CodesASCII.txt",
    _ADMIN1_MIRROR,
)
_COUNTRY = "RU"
_CHUNK = 400
# Alternate names longer than this are descriptions, not something a person types.
_ALIAS_LENGTH = 80
# Letters of the Russian alphabet. Other Cyrillic (Kazakh, Ossetian) is not the label.
_RUSSIAN = frozenset("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
_TO_LATIN = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
)


def _download(urls: tuple[str, ...]) -> bytes:
    """The first URL that returns a complete body. A stall tries the next mirror."""
    last: Exception | None = None
    for url in urls:
        try:
            # GeoNames is slow from some networks; one attempt is allowed five minutes.
            with urlopen(url, timeout=300) as response:  # noqa: S310 - GeoNames dump, not user input
                body: bytes = response.read()
        except (TimeoutError, OSError, IncompleteRead) as exc:
            last = exc
            continue
        if body.startswith(b"<!DOCTYPE") or body.startswith(b"<html"):
            last = RuntimeError(f"{url} returned a page, not the dump")
            continue
        return body
    if last is not None:
        raise last
    msg = "could not download the GeoNames dump"
    raise RuntimeError(msg)


def _regions(raw: bytes) -> dict[str, str]:
    """`RU.48` → the name GeoNames gives that first-level region."""
    found: dict[str, str] = {}
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        code, name, *_rest = line.split("\t")
        found[code] = name
    return found


def _is_russian(name: str) -> bool:
    letters = [char.casefold() for char in name if char.isalpha()]
    return bool(letters) and all(char in _RUSSIAN for char in letters)


def _folded_latin(name: str) -> str:
    return name.casefold().translate(_TO_LATIN).replace(" ", "").replace("-", "")


# Below this, the GeoNames name is an English exonym («Moscow»), not a transliteration.
_EXONYM_RATIO = 0.75
_STEM = 2
_STEM_LETTERS = 3


def _support(name: str, names: list[str]) -> int:
    """Latin aliases that are this name written in Latin letters."""
    folded = _folded_latin(name)
    return sum(1 for alias in names if not _is_russian(alias) and _folded_latin(alias) == folded)


def _same_spelling(names: list[str]) -> str:
    """«Казань» over «Казан» and «Къазан»; «Санкт-Петербург» over the spaced form."""
    pool = [name for name in names if "ъ" not in name.casefold()] or list(names)
    folded = {name.casefold() for name in pool}
    pool = [name for name in pool if f"{name.casefold()}ь" not in folded]
    hyphenated = [name for name in pool if "-" in name]
    same = {_folded_latin(name) for name in pool}
    if hyphenated and len(same) == 1:
        pool = hyphenated
    # «Тольятти» / «Ульяновск» keep the soft sign; «Толиати» does not.
    soft = [name for name in pool if "ь" in name.casefold()]
    stems = {name.casefold()[:_STEM_LETTERS] for name in pool}
    folds = {_folded_latin(name)[: _STEM_LETTERS + 1] for name in pool}
    if soft and (len(stems) == 1 or len(folds) == 1):
        pool = soft
    return min(pool, key=lambda name: (len(name), name))


def _cluster(names: list[str]) -> list[str]:
    """Names that share the longest common stem, so «Москва» wins over «Муско»."""
    if len(names) < _STEM:
        return names
    prefixes = {name[:length] for name in names for length in range(_STEM_LETTERS, len(name) + 1)}
    best_prefix = ""
    best_count = 1
    for prefix in prefixes:
        count = sum(name.startswith(prefix) for name in names)
        longer = count == best_count and len(prefix) > len(best_prefix)
        if count > best_count or longer:
            best_prefix = prefix
            best_count = count
    if best_count < _STEM:
        return names
    return [name for name in names if name.startswith(best_prefix)]


def russian_label(official: str, names: list[str]) -> str:
    """The Russian name. The GeoNames name stays when no Russian alias is listed."""
    russian = [name for name in names if _is_russian(name) and len(name) >= len("Сочи")]
    if not russian:
        return official
    target = _folded_latin(official)

    def score(name: str) -> float:
        return difflib.SequenceMatcher(None, _folded_latin(name), target).ratio()

    best = max(score(name) for name in russian)
    pool = [name for name in russian if score(name) >= best]
    if best < _EXONYM_RATIO:
        top = max(_support(name, names) for name in russian)
        if top:
            pool = _cluster([name for name in russian if _support(name, names) == top])
    return _same_spelling(pool)


def _aliases(name: str, ascii_name: str, alternate: str) -> list[tuple[str, str, bool]]:
    """`(stored name, folded name, official)` without duplicates."""
    seen: set[str] = set()
    rows: list[tuple[str, str, bool]] = []

    def add(value: str, *, primary: bool) -> None:
        text = value.strip()
        if not text or len(text) > _ALIAS_LENGTH:
            return
        norm = normalize_city_query(text)
        if not norm or norm in seen:
            return
        seen.add(norm)
        rows.append((text, norm, primary))

    add(name, primary=True)
    add(ascii_name, primary=False)
    for item in alternate.split(","):
        add(item, primary=False)
    return rows


_MIN_COLUMNS = 15
_POPULATION = 14
_COUNTRY_COLUMN = 8


def _places(
    archive: bytes, regions: dict[str, str]
) -> list[tuple[City, list[tuple[str, str, bool]]]]:
    places: list[tuple[City, list[tuple[str, str, bool]]]] = []
    with zipfile.ZipFile(BytesIO(archive)) as bundle:
        name = next(item for item in bundle.namelist() if item.endswith(".txt"))
        with bundle.open(name) as handle, TextIOWrapper(handle, encoding="utf-8") as lines:
            for line in lines:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < _MIN_COLUMNS or parts[_COUNTRY_COLUMN] != _COUNTRY:
                    continue
                aliases = _aliases(parts[1], parts[2], parts[3])
                if not aliases:
                    continue
                label = russian_label(parts[1], [alias for alias, _norm, _primary in aliases])
                label_norm = normalize_city_query(label)
                aliases = [(alias, norm, norm == label_norm) for alias, norm, _primary in aliases]
                region_code = f"{_COUNTRY}.{parts[10]}" if parts[10] else ""
                places.append(
                    (
                        City(
                            geoname_id=int(parts[0]),
                            name=label,
                            country_code=_COUNTRY,
                            region=regions.get(region_code),
                            latitude=float(parts[4]),
                            longitude=float(parts[5]),
                            feature_class=parts[6][:1],
                            feature_code=parts[7][:10],
                            population=int(parts[_POPULATION]) if parts[_POPULATION] else 0,
                        ),
                        aliases,
                    )
                )
    return places


async def import_cities(session: AsyncSession, archive: bytes, admin1: bytes) -> int:
    """Replace the dictionary. Callers import only into an empty table."""
    places = _places(archive, _regions(admin1))
    for start in range(0, len(places), _CHUNK):
        chunk = places[start : start + _CHUNK]
        session.add_all(city for city, _aliases in chunk)
        await session.flush()
        session.add_all(
            CityAlias(city_id=city.geoname_id, name=name, norm=norm, is_primary=primary)
            for city, aliases in chunk
            for name, norm, primary in aliases
        )
        await session.flush()
    return len(places)


def _report(gaps: list[CityResolutionGap]) -> None:
    if not gaps:
        print("Every stored city matched one place.")
        return
    print(f"Unresolved cities: {len(gaps)}. The original text was kept.")
    for gap in gaps:
        print(f"  {gap.entity} {gap.entity_id}: {gap.raw_value}")
    path = Path("/data/uploads/city-resolution-gaps.txt")
    try:
        path.write_text(
            "".join(f"{gap.entity}\t{gap.entity_id}\t{gap.raw_value}\n" for gap in gaps),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"The gap list is above. The report file was not written: {exc}")
    else:
        print(f"Report: {path}")


async def _run(
    *, if_missing: bool, archive: Path | None, admin1: Path | None, replace: bool
) -> int:
    sessionmaker = get_sessionmaker()
    try:
        async with sessionmaker() as session:
            loaded = await CityRepository(session).count()
            if replace and loaded:
                await session.execute(update(CandidateProfile).values(city_id=None))
                await session.execute(update(Vacancy).values(city_id=None))
                await session.execute(delete(CityResolutionGap))
                await session.execute(delete(CityAlias))
                await session.execute(delete(City))
                await session.commit()
                loaded = 0
            if loaded == 0:
                if archive is not None and admin1 is not None:
                    archive_bytes, admin1_bytes = await asyncio.to_thread(
                        lambda: (archive.read_bytes(), admin1.read_bytes())
                    )
                else:
                    print("Downloading the GeoNames city list…")
                    archive_bytes, admin1_bytes = await asyncio.to_thread(
                        lambda: (_download(CITIES_URLS), _download(ADMIN1_URLS))
                    )
                count = await import_cities(session, archive_bytes, admin1_bytes)
                await session.commit()
                print(f"Imported {count} Russian populated places.")
            elif if_missing:
                print(f"City dictionary is already loaded ({loaded} places).")
            else:
                print(
                    f"City dictionary already has {loaded} places. Not downloading again.",
                    file=sys.stderr,
                )
            gaps = await bind_stored_cities(session)
            await session.commit()
            # Names were loaded before the ids were copied onto the rows.
            rows = await session.scalars(select(CityResolutionGap).order_by(CityResolutionGap.id))
            gaps = list(rows.all())
            _report(gaps)
            # Touch the count so a failed flush is visible.
            await session.scalar(select(func.count()).select_from(City))
    finally:
        await get_engine().dispose()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.seed.cities")
    parser.add_argument(
        "--if-missing",
        action="store_true",
        help="download only when the dictionary is empty; always match stored cities",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="drop the dictionary and import again; stored city ids are matched afterwards",
    )
    parser.add_argument("--archive", type=Path, help="cities1000.zip already on disk")
    parser.add_argument("--admin1", type=Path, help="admin1CodesASCII.txt already on disk")
    args = parser.parse_args(argv)
    return asyncio.run(
        _run(
            if_missing=args.if_missing,
            archive=args.archive,
            admin1=args.admin1,
            replace=args.replace,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
