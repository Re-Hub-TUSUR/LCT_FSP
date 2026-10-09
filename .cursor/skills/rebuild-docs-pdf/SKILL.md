---
name: rebuild-docs-pdf
description: >-
  Regenerates the branded Russian product documentation PDF at the repository
  root. Use when the user asks to rebuild, regenerate, or refresh the
  documentation PDF, kadry-ru.pdf, or invokes this skill.
disable-model-invocation: true
---

# Rebuild the documentation PDF

Run one command from the repository root. Do not edit Markdown, the script, or the skill unless the user asked for a content change.

```bash
python scripts/build_pdf.py
```

The PDF is `kadry-ru.pdf` in the repository root. Source text is `docs-zensical/docs/ru/`. Chrome must be installed. The `markdown` package must be importable.

If the command fails because the sandbox blocks it, run the same command outside the sandbox.

When it finishes, tell the user the absolute path of `kadry-ru.pdf`. If a viewer already has the file open, they need to reopen it.
