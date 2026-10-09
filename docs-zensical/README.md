# KADRY documentation

Product and engineering documentation for **KADRY** — the FSP hiring platform (categorised candidates, employer outreach, salary bands, swipes, calendar, admin).

English and Russian sources live in `docs/en/` and `docs/ru/`. Normative behaviour is the **BRD**. The engineering section describes the current monorepo and does not override the BRD.

## With the stack

`docker compose up --build` from the repository root also starts this site. Open `http://localhost:8081`. The image builds the static site and serves it with nginx. It does not wait for the API.

## Local site

From this directory, without Docker:

```bash
pip install zensical
zensical serve
```

A static build:

```bash
zensical build --clean
```

Output goes to `site/` (gitignored). There is no deploy workflow in this repository.

## PDF

A branded A4 of the Russian site, with the FSP frieze and the product fonts:

```bash
python scripts/build_pdf.py
```

Chrome writes `kadry-ru.pdf` in this directory. The source of the text stays the Markdown.
