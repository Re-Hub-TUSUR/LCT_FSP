"""Print the Russian KADRY documentation as a branded A4 PDF.

The frieze is the same hybrid pattern as the product ornament: blue, ink, and red
glyphs from the FSP brandbook. Chrome writes the PDF; Markdown stays the source.
"""

from __future__ import annotations

import base64
import re
import subprocess
import sys
from pathlib import Path

import markdown

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs-zensical" / "docs"
FONTS = REPO / "frontend" / "src" / "shared" / "assets" / "fonts"
OUT_HTML = REPO / "docs-zensical" / ".cache" / "kadry-ru.html"
OUT_PDF = REPO / "kadry-ru.pdf"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

# Section, kicker, source path. Order matches the Russian nav in zensical.toml.
CHAPTERS: list[tuple[str, str]] = [
    ("Продукт", "ru/index.md"),
    ("Продукт", "ru/product/overview.md"),
    ("Продукт", "ru/product/pages.md"),
    ("Сценарии", "ru/use-cases/index.md"),
    ("Сценарии", "ru/use-cases/common.md"),
    ("Сценарии", "ru/use-cases/candidate.md"),
    ("Сценарии", "ru/use-cases/employer.md"),
    ("Сценарии", "ru/use-cases/admin.md"),
    ("Сценарии", "ru/user-flows/index.md"),
    ("Сценарии", "ru/user-flows/demo.md"),
    ("Сценарии", "ru/user-flows/candidate.md"),
    ("Сценарии", "ru/user-flows/employer.md"),
    ("Сценарии", "ru/user-flows/admin.md"),
    ("Бизнес", "ru/business/specification.md"),
    ("Бизнес", "ru/business/brd/index.md"),
    ("Бизнес", "ru/business/brd/01-auth.md"),
    ("Бизнес", "ru/business/brd/02-candidate-profile.md"),
    ("Бизнес", "ru/business/brd/03-assessment.md"),
    ("Бизнес", "ru/business/brd/04-invitations-chat.md"),
    ("Бизнес", "ru/business/brd/05-employer-matching.md"),
    ("Бизнес", "ru/business/brd/06-vacancies-tasks.md"),
    ("Бизнес", "ru/business/brd/07-admin.md"),
    ("Бизнес", "ru/business/brd/08-user-data.md"),
    ("Бизнес", "ru/business/brd/09-parameters.md"),
    ("Бизнес", "ru/business/nfr.md"),
    ("Бизнес", "ru/business/coverage.md"),
    ("Акторы", "ru/actors/personas.md"),
    ("Инженерия", "ru/technical/index.md"),
    ("Инженерия", "ru/technical/architecture.md"),
    ("Инженерия", "ru/technical/api.md"),
    ("Инженерия", "ru/technical/data-model.md"),
    ("Инженерия", "ru/technical/local-start.md"),
    ("Инженерия", "ru/technical/fsp-id.md"),
    ("Инженерия", "ru/technical/ats.md"),
    ("Инженерия", "ru/technical/implementation-status.md"),
    ("Глоссарий", "ru/glossary.md"),
]

# Glyphs of the brandbook frieze, in the ornament's order. Tones: b blue, w light, r red.
SIGNS: list[list[tuple[str, str]]] = [
    [("•", "r")],
    [("{", "w"), ("•", "r"), ("}", "w")],
    [("▲", "b")],
    [("{", "r"), ("//", "w"), ("}", "r")],
    [("•", "r")],
    [("<", "b"), ("/", "r"), (">", "b")],
    [("(", "b"), (")", "b")],
    [(">", "b"), ("|", "w"), ("<", "b")],
    [("━", "b")],
    [("▲", "w")],
    [("∿", "b")],
    [(":", "w"), (")", "b")],
    [("//", "r")],
    [("<", "b"), ("//", "w"), (">", "b")],
    [("⋮", "w")],
    [("[", "b"), ("•", "w"), ("/", "r"), ("]", "b")],
    [("•", "w"), ("━", "b")],
    [("{", "b"), ("}", "b")],
    [("•", "w")],
    [("|", "r")],
    [(">", "b")],
    [("•", "w")],
    [("|", "b")],
    [("<", "b"), ("/", "r"), (">", "b")],
    [("<", "b"), ("//", "r"), (">", "b")],
]


def frieze(kind: str) -> str:
    parts: list[str] = []
    for _ in range(6):
        for sign in SIGNS:
            glyphs = "".join(
                f'<span class="{tone}">{_esc(glyph)}</span>' for glyph, tone in sign
            )
            parts.append(f'<span class="sign">{glyphs}</span>')
    return f'<div class="frieze frieze--{kind}" aria-hidden="true">{"".join(parts)}</div>'


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def anchor(rel: str) -> str:
    return rel.removesuffix(".md").replace("/", "-").replace("\\", "-")


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        return re.sub(r"^---\r?\n.*?\r?\n---\r?\n", "", text, count=1, flags=re.S)
    return text


def mermaid_html(body: str) -> str:
    if "sequenceDiagram" in body:
        steps = [line.strip() for line in re.findall(r":\s*(.+)$", body, flags=re.M)]
    else:
        steps = re.findall(r'\w+\["([^"]+)"\]|\w+\{"([^"]+)"\}', body)
        steps = [left or right for left, right in steps]
    if not steps:
        return f"<pre><code>{_esc(body.strip())}</code></pre>"
    chips: list[str] = []
    for index, step in enumerate(steps):
        if index:
            chips.append('<span class="flow__arr">→</span>')
        chips.append(f'<span class="flow__step">{_esc(step)}</span>')
    return f'<div class="flow">{"".join(chips)}</div>'


def prepare_markdown(text: str, rel: str) -> str:
    text = strip_frontmatter(text)

    def mermaid_sub(match: re.Match[str]) -> str:
        return "\n\n" + mermaid_html(match.group(1)) + "\n\n"

    text = re.sub(r"```mermaid\r?\n(.*?)```", mermaid_sub, text, flags=re.S)

    def link_sub(match: re.Match[str]) -> str:
        label, href = match.group(1), match.group(2)
        if href.startswith(("http://", "https://", "#", "mailto:")):
            return match.group(0)
        target = href.split("#", 1)[0]
        if not target.endswith(".md"):
            return match.group(0)
        resolved = (Path(rel).parent / target).as_posix()
        resolved = Path(resolved).as_posix()
        # Collapse .. segments.
        parts: list[str] = []
        for part in resolved.split("/"):
            if part == "..":
                if parts:
                    parts.pop()
            elif part not in ("", "."):
                parts.append(part)
        return f"[{label}](#{anchor('/'.join(parts))})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_sub, text)


def _nobr_ids(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        plain = re.sub(r"<[^>]+>", "", inner).strip()
        if len(plain) <= 18 and "-" in plain and re.match(r"(П|FR|UC|NFR|G\d)", plain):
            return f'<td class="id">{inner}</td>'
        return match.group(0)

    return re.sub(r"<td>(.*?)</td>", repl, html, flags=re.S)


def first_heading(html: str, fallback: str) -> str:
    match = re.search(r"<h1>(.*?)</h1>", html, flags=re.S)
    if not match:
        return fallback
    return re.sub(r"<[^>]+>", "", match.group(1)).strip()


def render_chapter(section: str, rel: str, *, opens: bool) -> tuple[str, str]:
    source = (DOCS / rel).read_text(encoding="utf-8")
    body = markdown.markdown(
        prepare_markdown(source, rel),
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    body = re.sub(
        r"<h2>([^<]*FR-[^<]*)</h2>",
        r'<h2 class="req">\1</h2>',
        body,
    )
    body = _nobr_ids(body)
    title = first_heading(body, Path(rel).stem)
    kind = "article opens" if opens else "article"
    html = (
        f'<article class="{kind}" id="{anchor(rel)}">'
        f'<p class="kicker">{_esc(section)}</p>'
        f"{frieze('paper')}"
        f"{body}"
        f"</article>"
    )
    return title, html


def font_face() -> str:
    mono = base64.b64encode((FONTS / "JetBrainsMono-Variable.ttf").read_bytes()).decode()
    display = base64.b64encode((FONTS / "TDAText.ttf").read_bytes()).decode()
    return f"""
@font-face {{
  font-family: "JetBrains Mono";
  src: url("data:font/ttf;base64,{mono}") format("truetype");
  font-weight: 100 800;
  font-style: normal;
}}
@font-face {{
  font-family: "TDAText";
  src: url("data:font/ttf;base64,{display}") format("truetype");
  font-weight: 400;
  font-style: normal;
}}
"""


CSS = r"""
@page {
  size: A4;
  margin: 16mm 14mm 16mm 14mm;
  @bottom-left {
    content: "KADRY  ·  Документация";
    font-family: "JetBrains Mono", monospace;
    font-size: 8pt;
    letter-spacing: 0.08em;
    color: #6e6f75;
  }
  @bottom-right {
    content: counter(page);
    font-family: "JetBrains Mono", monospace;
    font-size: 9pt;
    font-weight: 700;
    color: #402fff;
  }
}
@page:first {
  margin: 0;
  @bottom-left { content: none; }
  @bottom-right { content: none; }
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  color: #1b1c21;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 9.5pt;
  line-height: 1.55;
  font-weight: 450;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.cover {
  height: 297mm;
  background: #141519;
  color: #ededed;
  padding: 18mm 16mm 16mm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  break-after: page;
}
.cover__top, .cover__bottom { flex: none; }
.cover__mid { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.eyebrow {
  margin: 14mm 0 8mm;
  font-size: 10pt;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #9b9c9e;
}
.wordmark {
  margin: 0;
  font-family: "TDAText", "JetBrains Mono", sans-serif;
  font-size: 78pt;
  font-weight: 400;
  line-height: 0.9;
  letter-spacing: 0.04em;
  color: #ededed;
}
.cover__rule {
  width: 42mm;
  height: 3px;
  margin: 8mm 0;
  background: #ec1d35;
}
.cover__title {
  margin: 0;
  font-size: 16pt;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #ededed;
}
.cover__lead {
  max-width: 140mm;
  margin: 6mm 0 0;
  color: #b5b6b9;
  font-size: 11pt;
  line-height: 1.5;
}
.cover__meta {
  margin: 10mm 0 0;
  color: #402fff;
  font-size: 9pt;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.frieze {
  display: flex;
  align-items: center;
  gap: 0.55em;
  overflow: hidden;
  white-space: nowrap;
  height: 1.15em;
  font-weight: 800;
  font-size: 11pt;
  line-height: 1;
}
.frieze .sign { display: inline-flex; gap: 0; flex: none; }
.frieze--dark .b { color: #402fff; }
.frieze--dark .w { color: #ededed; }
.frieze--dark .r { color: #ec1d35; }
.frieze--paper .b { color: #402fff; }
.frieze--paper .w { color: #1b1c21; }
.frieze--paper .r { color: #ec1d35; }

.toc { break-after: page; }
.toc h1 { margin-top: 4mm; }
.toc ol { list-style: none; margin: 6mm 0 0; padding: 0; }
.toc li { break-inside: avoid; }
.toc a {
  display: flex;
  justify-content: space-between;
  gap: 8mm;
  padding: 2.2mm 0;
  border-bottom: 1px solid #e4e4e8;
  color: #1b1c21;
  text-decoration: none;
  font-weight: 500;
}
.toc .sec {
  color: #402fff;
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  min-width: 28mm;
}

article { margin-top: 9mm; }
article.opens { break-before: page; margin-top: 0; }
article .frieze { margin: 0 0 5mm; }
.kicker {
  margin: 0 0 3mm;
  color: #ec1d35;
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 6mm;
  font-size: 18pt;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
  color: #1b1c21;
}
h2 {
  margin: 7mm 0 2.5mm;
  font-size: 11.5pt;
  font-weight: 700;
  line-height: 1.3;
  color: #1b1c21;
  break-after: avoid;
}
h2.req {
  margin-top: 8mm;
  padding: 1.5mm 0 1.5mm 3mm;
  border-left: 2.5px solid #ec1d35;
  color: #1b1c21;
}
h3 {
  margin: 5mm 0 1.5mm;
  font-size: 10pt;
  font-weight: 700;
  color: #402fff;
  break-after: avoid;
}
p { margin: 0 0 3mm; }
strong { font-weight: 700; }
a { color: #402fff; text-decoration: none; }
ul, ol { margin: 0 0 3.5mm; padding-left: 5mm; }
li { margin: 0.6mm 0; }
li::marker { color: #402fff; }

table {
  width: 100%;
  margin: 3mm 0 5mm;
  border-collapse: collapse;
  font-size: 8pt;
  line-height: 1.4;
}
th {
  background: #1b1c21;
  color: #ededed;
  font-weight: 700;
  text-align: left;
  padding: 2mm 2.2mm;
}
td {
  padding: 1.8mm 2.2mm;
  border-bottom: 1px solid #e4e4e8;
  vertical-align: top;
}
td.id { white-space: nowrap; }
tr { break-inside: avoid; }
tbody tr:nth-child(even) td { background: #f4f4f6; }

code {
  font-family: "JetBrains Mono", monospace;
  font-size: 0.92em;
  color: #402fff;
  background: #ececf2;
  padding: 0 0.25em;
}
pre {
  margin: 3mm 0 4mm;
  padding: 3.5mm 4mm;
  background: #1b1c21;
  color: #ededed;
  border-left: 3px solid #ec1d35;
  white-space: pre-wrap;
  break-inside: avoid;
}
pre code { color: inherit; background: none; padding: 0; font-size: 8pt; }

.flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1.5mm 0;
  margin: 3mm 0 5mm;
  padding: 3.5mm;
  background: #f4f4f6;
  border-left: 3px solid #402fff;
}
.flow__step {
  background: #fff;
  border: 1px solid #d5d5dc;
  padding: 1.2mm 2.2mm;
  font-size: 8pt;
  font-weight: 700;
}
.flow__arr {
  color: #ec1d35;
  padding: 0 1.6mm;
  font-weight: 700;
}
"""


def build_html() -> str:
    toc: list[str] = []
    chapters: list[str] = []
    opened: set[str] = set()
    for section, rel in CHAPTERS:
        path = DOCS / rel
        if not path.exists():
            raise SystemExit(f"missing chapter: {rel}")
        title, html = render_chapter(section, rel, opens=section not in opened)
        opened.add(section)
        toc.append(
            "<li>"
            f'<a href="#{anchor(rel)}">'
            f'<span class="sec">{_esc(section)}</span>'
            f"<span>{_esc(title)}</span>"
            "</a></li>"
        )
        chapters.append(html)

    cover = f"""
<section class="cover">
  <div class="cover__top">{frieze("dark")}</div>
  <div class="cover__mid">
    <p class="eyebrow">ФСП · платформа подбора</p>
    <p class="wordmark">KADRY</p>
    <div class="cover__rule"></div>
    <p class="cover__title">Документация продукта</p>
    <p class="cover__lead">Требования, экраны, сценарии и устройство текущего продукта. Текст совпадает с русской документацией на сайте.</p>
    <p class="cover__meta">2026</p>
  </div>
  <div class="cover__bottom">{frieze("dark")}</div>
</section>
"""
    toc_html = (
        '<section class="toc">'
        '<p class="kicker">Содержание</p>'
        + frieze("paper")
        + "<h1>Содержание</h1><ol>"
        + "".join(toc)
        + "</ol></section>"
    )
    return (
        "<!DOCTYPE html><html lang=\"ru\"><head><meta charset=\"utf-8\">"
        f"<title>KADRY — документация</title><style>{font_face()}{CSS}</style></head><body>"
        f"{cover}{toc_html}{''.join(chapters)}</body></html>"
    )


def main() -> None:
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(build_html(), encoding="utf-8")
    if not CHROME.exists():
        raise SystemExit(f"Chrome not found: {CHROME}")
    subprocess.run(
        [
            str(CHROME),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={OUT_PDF}",
            OUT_HTML.as_uri(),
        ],
        check=True,
    )
    print(OUT_PDF)


if __name__ == "__main__":
    sys.exit(main())
