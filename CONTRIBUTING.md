# Contributing / Conventions

These conventions mirror the [situation-report](https://github.com/Jaegerfeld/situation-report)
project, so quality standards stay consistent across projects. They apply to all five Star
Citizen tools ([Bauplan-Planer](https://github.com/Jaegerfeld/StarCitizen-Bauplan-Planer),
[Wikelo-Planer](https://github.com/Jaegerfeld/StarCitizen-Wikelo-Planer),
[Handels-Planer](https://github.com/Jaegerfeld/StarCitizen-Handels-Planer),
[Schiffskauf-Planer](https://github.com/Jaegerfeld/StarCitizen-Schiffskauf-Planer),
[Screenshot-Auswerter](https://github.com/Jaegerfeld/StarCitizen-Screenshot-Auswerter)),
scaled to their size: a small stdlib Python build step plus a self-contained HTML app.

## Quality gate

- **Lint:** [ruff](https://docs.astral.sh/ruff/) — rule sets `F, I, B, UP, C901`,
  line length 100, max cyclomatic complexity 15 (see [`pyproject.toml`](pyproject.toml)).
- **CI:** [`.github/workflows/quality.yml`](.github/workflows/quality.yml) runs `ruff check .`
  on every push/PR. ruff is **pinned** (`0.15.*`) so CI matches local.
- Run locally before pushing:

  ```bash
  pip install "ruff==0.15.*"
  python -m ruff check .
  ```

## Comments and docstrings

Same standard as situation-report.

1. **Header block in every source file** (Python, PowerShell; German), right at the top:

   ```python
   # =============================================================================
   # Autor:          Robert Seebauer
   # Repository:     https://github.com/Jaegerfeld/<repo>
   # KI-Unterstützung: Erstellt mit Unterstützung von Claude (Anthropic)
   # Erstellt:       DD.MM.YYYY
   # Geändert:       DD.MM.YYYY
   # Lizenz:         BSD-3-Clause (siehe LICENSE)
   #
   # Fachliche Funktion:
   #   What the file does in the tool, for whom, and which decisions stand
   #   behind it (data sources, limits, deliberate deviations).
   # =============================================================================
   ```

   HTML page templates carry the same block as an `<!-- … -->` comment after the doctype.
   Update **Geändert** with every substantive change.
2. **Docstrings in English**, Google style. Every public function and class has one; private
   helpers get one when name and three lines of code don't make the purpose obvious.
   Non-trivial functions list `Args:`, `Returns:` and, if they raise, `Raises:`. Meaningful
   module constants get a `#:` comment.
3. **JavaScript in the pages** (English): sections with `/* ---------- section ---------- */`;
   every non-trivial function gets a one-line `// …` comment directly above it.
4. Comments explain the **why** (data format, game quirk, special case), not what the code
   already says.
5. **Shared files** [`kopfzeile.py`](kopfzeile.py) (header and "What's new?" dialog) and
   [`sc_design.py`](sc_design.py) (design tokens, responsive rules) are **byte-identical in all
   five repos**. Change them in one place, copy to all five, and compare the md5 sums.

## Versioning & changelog

- **[SemVer](https://semver.org/)** in [`version.py`](version.py) — the single source of truth
  (shown next to the page title). Bump: patch = fixes/wording, minor = features, major = breaking.
- Keep a **[CHANGELOG.md](CHANGELOG.md)** in the *Keep a Changelog* format; one entry per
  release. It is baked into the page and shown in the "What's new?" dialog, so update it
  **before** the final build.

## Branches & deploy

- Do non-trivial work on a **feature branch**; open a PR against `main`.
- `main` auto-builds and deploys to GitHub Pages, so **never push a broken intermediate state
  to `main`** — merge only once the build and checks are green.
- Verify data-shaping changes against a **golden reference** (diff the produced data against the
  previous known-good output) before merging.

## Docs & reach

- **Bilingual**: user-facing docs and UI in **English and German**
  ([`README.md`](README.md) EN, [`README.de.md`](README.de.md) DE).
- Prefer **self-contained, offline-capable** deliverables with **no external runtime deps**
  (standard library only) where feasible.
- The pages work on desktop first and optionally on phones and tablets (tabs below 920 px,
  44 px touch targets); check both when changing the layout.
- **Credit data sources** in the README.

## AI-assisted development

These projects are developed largely with AI ([Claude Code](https://claude.com/claude-code));
state that openly in the README.
