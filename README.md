# blind-survey

An anonymous survey run as an interview with an AI model, producing short
neutral statements you can count and cluster. It is built for a program manager
who wants candid input from a group — grantees, a team, a cohort — and who is
not technical.

Every prompt and rule is a markdown file you can read and argue with. There is
no hosted service and no account of ours in the loop.

## How it works

A respondent pastes a compiled prompt into their own AI model account. It
interviews them for about fifteen minutes (configurable via
`survey.duration_minutes`) about whatever audience `survey.yaml` names — this
checkout ships configured for maintainers and funders across an open source
ecosystem, not any single organization — then drafts short neutral statements
of what they said and asks them to keep, edit, or cut each one. Only what they
keep leaves the conversation — as a block of text they paste, themselves, into
a form that asks for no name, no email, and no login.

`tools/ingest.py` pulls the submissions, writing one file per submission that
holds the answer text and nothing else. Two analysis prompts turn those bullets
into `statements.jsonl`, which `tools/breadth.py` counts and `/analyze` clusters.

Two boundaries do the work:

- **At the end of each interview**, the respondent decides statement by
  statement what crosses out of their private conversation. The interview
  prompt holds no API key and no submit button.
- **At ingest**, deduplication runs on the submission id alone — Tally's `id`
  field, or Google's `responseId`. Tally's `respondentId`, `createdAt`,
  `pdfUrl`, `previewUrl`, and Google's own timestamps are never read at all.
  `private/manifest.txt` holds one `sha256:` digest of a submission id per
  line, sorted so its order carries no relationship to the pool. That holds
  only because one script touches the submissions endpoint, never a
  conversational tool.

## Getting started

Clone the repository, point your coding agent at the folder, and say `/setup`.
It asks who is answering and roughly how many, what you are trying to learn, and
which questions to ask; writes `survey.yaml`; compiles the interview; and sets up
the form. On Tally it creates the form for you through the API. On Google Forms
you copy a pre-configured template in Drive and your agent walks you through a
short checklist in the Forms UI, since the Forms API won't let you set sign-in
at all, and won't report back whether the per-response cap or response editing
are on, either.

| Skill | What it does |
| --- | --- |
| `/setup` | Interviews you, writes `survey.yaml`, compiles `dist/`, creates and verifies the form. |
| `/administer` | Distributes the prompt and form together, and re-verifies the form before every pull. |
| `/ingest` | Pulls submissions into `private/pool/`, then screens what landed there. |
| `/analyze` | Two fresh sessions: bullets to statements, then statements to clusters and findings. |

## What this does not protect against

- **The interviewer is prompt behavior, not enforced behavior.** Checking a
  statement for who it points to, warning about a small group, and rewriting
  someone out of their distinctive phrasing are things `dist/interview.md` asks
  a model to do, in an account this repo does not control. No test here covers
  it. The respondent seeing every statement before it moves is the actual
  safeguard.
- **Provider metadata stays off disk; typed text is carried through.** If a
  respondent types their own name into the contribution block, ingest writes it
  faithfully, because to the tool that text is just the answer.
  `tools/check_pool.py` screens the pool afterwards for a leaked provider
  field — its headline purpose — plus emails, dates, and links, and it advises
  rather than decides: a hit needs a person to read the line.
- **Group size is a limit no tool changes.** At five or six respondents,
  distinctive content identifies its author whatever the channel does.
  `min_cell_size` governs how a count gets reported, not whether a sentence
  gives someone away.
- **Google Forms verification is partial.** Sign-in cannot be set through the
  Forms API at all, and none of the three settings the spec cares about —
  sign-in, capping one response per person, and response editing — can be
  read back through it either, so `tools/verify_form.py` reports all three as
  `cannot check`.

## Tally or Google Forms

Tally's API reports every setting the blind spec names — one required
`TEXTAREA` and no other input block, no email or captcha block, self and
respondent notifications off, no partial submissions, no `uniqueSubmissionKey`,
no `submissionsLimit`, no password, the form published and not closed. So
`tools/verify_form.py` is a real diff against the live form, and a violation
fails loudly before a respondent sees it. That API is free on every Tally
plan.

Google Forms is the fallback for an organization that needs to stay inside
Workspace. Of the settings the spec names, its API reports one —
`emailCollectionType` — and `verify_form.py` prints the other three as `cannot
check`. `/administer` re-runs the check before every pull, which narrows the
window in which someone flips one by hand. It does not close it.

Paper is the last resort: no API, no verification, everything typed in and
deduplicated by hand. See `skills/operator/administer/SKILL.md`.

## Quickstart

```bash
uv sync
uv run pytest -q
uv run python build/compile.py                  # rebuild dist/ from survey.yaml
uv run python tools/verify_form.py --from-file tests/fixtures/tally-form-compliant.json
uv run python tools/breadth.py examples/oso-ecosystem/statements.jsonl role
```

The last command runs against the worked example this checkout ships with. It
prints a breadth tally per value of the `role` facet: a figure where a figure
cannot point at anyone, otherwise one of the phrases from
`rules/quantifiers.md` — four of the six, since the other two are judgment
calls a person makes. Read that rule file before quoting a figure. The tally
counts statements, not people, and the example's largest cell comes back as 15
from a pool of six submissions.

## Layout

| Path | What's there |
| --- | --- |
| `survey.yaml` | The instrument. The one file you are likely to hand-edit. |
| `rules/` | Anonymity, statement style, breadth vocabulary. Inlined into `dist/`. |
| `schema/statement.md` | What a statement record holds, and what it omits. |
| `skills/participant/interview/` | The interview prompt source. Compiles to `dist/interview.md`. |
| `templates/trust-brief.md` | The respondent-facing brief. Compiles to `dist/trust-brief.md`. |
| `skills/operator/` | `/setup`, `/administer`, `/ingest`, `/analyze`. |
| `build/compile.py` | Resolves `include` and `{{ }}` markers against `survey.yaml`. |
| `tools/` | `config.py`, `validate.py`, `breadth.py`, `check_pool.py`, `verify_form.py`, `ingest.py`. |
| `examples/oso-ecosystem/` | A worked example: a pool of submissions and its statements. |
| `dist/`, `private/` | Generated artifacts and engagement data. Both gitignored. |

## License

Apache-2.0. See `LICENSE`.
