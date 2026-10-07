import json
import sys
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from app.schemas.assessment import CodePayload
from app.seed.code_bank import CodeTask, build, easy, hard, medium

OUT_DIR: Final = Path(__file__).parents[1] / "data" / "assessment" / "code"
MODULES: Final[dict[str, list[CodeTask]]] = {
    "easy": easy.TASKS,
    "medium": medium.TASKS,
    "hard": hard.TASKS,
}


def render(tasks: list[CodeTask]) -> str:
    rows = [build(task) for task in tasks]
    for row in rows:
        try:
            CodePayload.model_validate(
                {key: row[key] for key in ("time_limit", "groups", "reference")}
            )
        except ValidationError as exc:
            msg = f"{row['key']}: {exc}"
            raise ValueError(msg) from exc
    return json.dumps(rows, ensure_ascii=False, indent=1) + "\n"


def main(check: bool) -> int:
    stale = []
    for name, tasks in MODULES.items():
        path = OUT_DIR / f"{name}.json"
        text = render(tasks)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(path.name)
            continue
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"{path.name}: {len(tasks)} tasks")
    if stale:
        print(f"Out of date, rebuild with `python -m app.seed.code_bank`: {', '.join(stale)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv[1:]))
