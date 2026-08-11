# blind-survey

BYOM ("bring your own model") anonymous survey run as an interview with an AI.
It produces short neutral statements you can count and cluster. Every rule and
prompt is a markdown file you can read and amend for your use case. Responses
can be submitted via Tally or Google Forms.

## How it works

A respondent pastes a compiled prompt into their own AI model account. It
interviews them for about fifteen minutes, drafts short neutral statements, and
asks them to keep, edit, or cut each one. Only what they keep leaves, pasted by
them into a form that asks for no name, no email, and no login.

`tools/ingest.py` writes one file per submission, holding the answer text and
nothing else. Two analysis prompts turn those into `statements.jsonl`.

Two boundaries carry the anonymity:

- The respondent alone decides what leaves their conversation. The prompt has no
  API key and no submit button.
- Ingest keys on the submission id only. `respondentId`, timestamps, and PDF
  links are never read. `private/manifest.txt` holds sorted `sha256:` digests,
  so its order says nothing about the pool.

## Getting started

Clone it, point your coding agent at the folder, and say `/setup`.

| Skill | Does |
| --- | --- |
| `/setup` | Interviews you, writes `survey.yaml`, compiles `dist/`, creates and verifies the form. |
| `/administer` | Hands out prompt and form; re-verifies the form before every pull. |
| `/ingest` | Pulls submissions into `private/pool/`, then screens them. |
| `/analyze` | Bullets to statements, then statements to clusters. |

## What it does not protect against

- **The interviewer.** Its sign-off discipline is prompt behavior, in an account
  this repo does not control. No test covers it.
- **Text the respondent types.** Provider metadata stays off disk; a name typed
  into the answer does not. `check_pool.py` flags it and advises.
- **Small groups.** At five or six people, distinctive content identifies its
  author whatever the channel does.
- **Google Forms.** Three settings are absent from its API, so
  `verify_form.py` reports them as `cannot check`.

## Tally or Google Forms

Tally's API reports every setting the blind spec names, so `verify_form.py` is a
real diff against the live form and a violation fails loudly. It is free on
every plan. Google's API reports one of them, so verification is partial. Paper
works too, by hand.

## Quickstart

```bash
uv sync
uv run pytest -q
uv run python tools/compile.py
uv run python tools/breadth.py example/statements.jsonl subject_role --pool example/pool
```

The last command tallies the worked example: every cell as a phrase from
`rules/quantifiers.md`, never a bare count standing for people, alongside the
statement and submission counts so the ceiling on headcount is visible for
free.

## Layout

| Path | |
| --- | --- |
| `survey.yaml` | The instrument. The one file you will hand-edit. |
| `rules/` | Doctrine. Inlined into `dist/`. |
| `prompts/` | The interview prompt and the trust brief. Inlined into `dist/`. |
| `skills/` | The four skills: setup, administer, ingest, analyze. |
| `tools/` | The compiler and the checks. |
| `example/` | A worked example you can run. |
| `dist/`, `private/` | Generated output and survey data. Both gitignored. |

## License

Apache-2.0.
