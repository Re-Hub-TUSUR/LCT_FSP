"""CSV that Excel opens as is: UTF-8 with BOM, `;` between fields."""

import csv
import io
from collections.abc import Iterable, Sequence
from typing import Any

from fastapi.responses import Response

BOM = "﻿"


def _cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "да" if value else "нет"
    if isinstance(value, float):
        # Excel with the Russian locale reads a comma as the decimal separator.
        return f"{value:g}".replace(".", ",")
    if isinstance(value, list | tuple):
        return ", ".join(str(item) for item in value)
    return value


def render(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_cell(value) for value in row])
    return BOM + buffer.getvalue()


def csv_response(filename: str, headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> Response:
    """`filename` must be ASCII: it goes into a header."""
    return Response(
        content=render(headers, rows).encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
