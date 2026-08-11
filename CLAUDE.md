# CLAUDE.md

Orientation for an agent landing in this repo. Figure out which role you're
in before you touch anything — the three roles want different care.

## Which role are you in?

- **Setting up a survey, for a program manager who is not technical.**
  You're running `/setup`. Follow `skills/operator/setup/SKILL.md` exactly.
  You do the interviewing, the YAML editing, the form creation, and the
  reporting back — they never open a terminal.
- **Operating a survey that's already fielded.** You're running
  `/administer`, `/ingest`, or `/analyze`. Follow the matching skill under
  `skills/operator/`. You have no reason to read the pool for its content
  during administration — answer process questions, not content questions.
- **Changing the protocol itself.** You're editing `rules/`, `schema/`,
  `skills/participant/`, `templates/`, or the code under `build/` and
  `tools/`. Read the invariants below before you start.

## Invariants

- `dist/` is generated. Never hand-edit it. Author under
  `skills/participant/` and `templates/`, then run
  `uv run python build/compile.py`.
- `private/` never commits. That `.gitignore` entry is part of the
  anonymity design, not housekeeping — never weaken it, even temporarily.
- `rules/` is inlined into both compiled artifacts (`dist/interview.md`,
  `dist/trust-brief.md`). Editing a rule changes what a respondent actually
  reads, not just internal documentation. Recompile and re-run the tests
  after any change under `rules/`.
- Every facet enum in `survey.yaml` must include `unspecified`.
  `tools/config.py` enforces this at load time, so the analyzer is never in
  a position to resolve an ambiguous referent by guessing.
- Counts come only from `tools/breadth.py`. Never write a count by hand —
  not in a finding, not in a run note, not in a code comment.
- Form creation may go through MCP (the Tally MCP server, from `/setup`).
  Submissions never do. Only `tools/ingest.py`, invoked directly, ever
  touches a submissions endpoint — handing one to a conversational tool
  puts provider metadata in an agent's context, which is exactly what the
  pipeline is built to avoid. See `skills/operator/ingest/SKILL.md`.
- Every CLI module under `build/` and `tools/` needs the `sys.path` shim
  near its top:

  ```python
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  ```

  `uv run python tools/<name>.py` — the documented invocation, since this
  repo's audience can't be asked to know about `-m` — only puts the file's
  own directory on `sys.path`, not the repo root, and every module imports
  `tools.config` absolutely. Without the shim it dies with
  `ModuleNotFoundError` the moment it's run as a bare script, even though
  pytest never notices (`pyproject.toml` sets `pythonpath = ["."]`). This
  regressed four separate times during the initial build, always because a
  test called the module's function directly instead of spawning the
  process. `tests/test_cli_entrypoints.py` exists specifically to catch it
  again — run the suite after touching any import at the top of a CLI
  module.

## Voice, for anything a respondent reads

Anything that compiles into `dist/` — the interview prompt, the trust
brief, and every rule file inlined into them — is read by a respondent, not
a maintainer. Plain declarative sentences, the kind someone would say
aloud without irony. No protocol vocabulary: "atomize", "corroborate",
"provenance", "constituency", "falsifiable" are banned and
`tests/test_artifacts.py` and `tests/test_doctrine.py` check for them. No
disclaimer-speak, and no softening a limit into a maybe when it is in fact
certain — say what's true, including the parts that don't flatter the
design.

## The two commands

```bash
uv run python build/compile.py   # rebuild dist/ from survey.yaml + rules/ + skills/participant/ + templates/
uv run pytest -q                 # the whole suite — run after any change under rules/, tools/, build/, or survey.yaml
```
