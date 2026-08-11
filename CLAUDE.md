# CLAUDE.md

Orientation for an agent landing in this repo. Work out your role before you
touch anything.

## Which role are you in?

- **Setting up a survey** for a non-technical program manager. Run `/setup` and
  follow `skills/operator/setup/SKILL.md` exactly. You do the interviewing, the
  YAML, the form creation, and the reporting back; they never open a terminal.
- **Operating a fielded survey.** Run `/administer`, `/ingest`, or `/analyze`,
  following the matching skill under `skills/operator/`. During administration,
  answer process questions, not content questions. You have no reason to read
  the pool's content.
- **Changing the protocol.** You're editing `rules/`, `schema/`,
  `skills/participant/`, `templates/`, `build/`, or `tools/`. Read the
  invariants first.

## Invariants

- `dist/` is generated. Never hand-edit it. Author under `skills/participant/`
  and `templates/`, then run `uv run python build/compile.py`.
- `private/` never commits. That `.gitignore` entry is part of the anonymity
  design, not housekeeping — never weaken it, even temporarily.
- `rules/` is inlined into `dist/interview.md` and `dist/trust-brief.md`, so
  editing a rule changes what a respondent reads. Recompile and re-run the
  tests after any change under `rules/`.
- Every facet enum in `survey.yaml` must include `unspecified`.
  `tools/config.py` enforces this at load time, so the analyzer never guesses
  an ambiguous referent.
- Counts come only from `tools/breadth.py`. Never write one by hand, in a
  finding, a run note, or a code comment.
- Form creation may go through MCP (the Tally MCP server, from `/setup`).
  Submissions never do: only `tools/ingest.py`, invoked directly, ever touches
  a submissions endpoint, because handing one to a conversational tool puts
  provider metadata in an agent's context. See
  `skills/operator/ingest/SKILL.md`.
- Every CLI module under `build/` and `tools/` needs the `sys.path` shim near
  its top:

  ```python
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  ```

  A bare `uv run python tools/<name>.py` puts only the file's own directory on
  `sys.path`, so without the shim the absolute `tools.config` import dies with
  `ModuleNotFoundError` (pytest hides this: `pyproject.toml` sets
  `pythonpath = ["."]`). `tests/test_cli_entrypoints.py` catches it. Run the
  suite after touching any import at the top of a CLI module.

## Voice, for anything a respondent reads

Everything compiled into `dist/` is read by a respondent, not a maintainer.
Plain declarative sentences. No protocol vocabulary: "atomize", "corroborate",
"provenance", "constituency", "falsifiable" are banned, and
`tests/test_artifacts.py` and `tests/test_doctrine.py` check. No
disclaimer-speak, and never soften a certain limit into a maybe.

## The two commands

```bash
uv run python build/compile.py   # rebuild dist/ from survey.yaml + rules/ + skills/participant/ + templates/
uv run pytest -q                 # run after any change under rules/, tools/, build/, or survey.yaml
```
