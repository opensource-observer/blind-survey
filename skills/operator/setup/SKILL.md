# setup — field a survey with no form builder and no terminal

## Who you are talking to

A program manager who is not technical. They never open a form builder, write
YAML, or run a command. You do all of that and report back in plain language.

## The interview

Ask one question at a time; wait for an answer before the next. For every
choice, say what you would pick and why in one sentence, then ask. Never hand
over a bare menu.

1. **Audience and size.** Who is answering, and roughly how many people? Get a
   number even if it's a guess: it sets how breadth is reported, and both compiled
   documents state it to respondents.
2. **What they want to learn.** What is the survey answering, and what would
   change their mind? If they can't say, it is scoped too broadly.
3. **Questions.** Propose the set already in `survey.yaml` — worked for sensing
   across an open source ecosystem — and let them keep, edit, or replace them.
4. **Length.** Recommend the shipped fifteen minutes unless they push back.
5. **Provider.** Recommend Tally: free API on every plan, and every setting the
   blind spec cares about reads back through it. Google Forms only to stay inside
   a Workspace organization; paper as a last resort. Say what each costs in
   verification before they pick.

`min_cell_size` follows from the group size in question 1. Below about ten
people, breadth stays qualitative whatever number goes in the field — say so
when you recommend a value.

## Write survey.yaml

Fill in every key, not only the ones the conversation touched: `name`, `title`,
`audience`, `duration_minutes`, `submission` (`provider`, `field_label`,
`block_header`; leave `form_id` and `form_url` null for now), `anonymity`
(`expected_respondents`, `min_cell_size`), `questions`, `facets`, `stoplist`.

Every list under `facets` needs `unspecified`, or the loader rejects it. Seed
`stoplist` with the organization's own name if they gave you one. Hand-editing
`survey.yaml` later is fine.

## Compile

```bash
uv run python build/compile.py
```

This writes `dist/interview.md`, the prompt a respondent is handed, and
`dist/trust-brief.md`, what they read first. Read `dist/interview.md` yourself:
the build catches an unresolved marker, not wording that's wrong for this
audience.

## Create the form

**Tally.**

- Prefer the MCP server at `https://api.tally.so/mcp` if connected
  (`claude mcp add tally --transport http https://api.tally.so/mcp`, over HTTP
  with OAuth or a bearer key). It's in beta — fall back to the API if it
  misbehaves.
- Create the form with a `POST` to `https://api.tally.so/forms` (or the MCP
  equivalent) using `TALLY_API_KEY`. The API costs nothing on any plan.
- Exactly one input block: a required `TEXTAREA` labeled exactly the value of
  `submission.field_label`. No other input block, no email or captcha block.
- Set `hasSelfEmailNotifications: false`, `hasRespondentEmailNotifications:
  false`, `hasPartialSubmissions: false`. Leave `uniqueSubmissionKey` and
  `submissionsLimit` unset, and `password: null`. Publish so
  `status: PUBLISHED`.

**Google Forms.**

- `FormSettings` carries only `quizSettings` and `emailCollectionType`. Set
  `emailCollectionType: DO_NOT_COLLECT` and add one required paragraph question.
- Requiring sign-in, capping one response per person, and allowing response
  editing are absent from the API in both directions, so a form built through it
  cannot come out with any of them turned on.
- Standing up a GCP project and OAuth client is not reasonable to ask of this
  program manager, so use a pre-configured template form they copy in Drive — a
  copy inherits its settings — then confirm by hand in the UI: sign-in off, no
  per-response limit, editing off.

Either provider: write the resulting `form_id` and `form_url` back into
`survey.yaml` once the form exists.

## Verify

```bash
uv run python tools/verify_form.py
```

Any violation stops setup here — fix the form, don't argue with the tool. Read
its `cannot check` lines aloud to the program manager. On a Google Form there
will be three — sign-in, the per-response limit, and editing — because the API
cannot see any of them, which is why `/administer` re-runs this check before
every pull.

## Probe end to end

Be a respondent yourself before a real one is:

1. Submit a throwaway block through the live form.
2. Ingest it: `uv run python tools/ingest.py`.
3. Open the pool file it wrote; confirm it holds exactly the block you pasted and
   nothing else.
4. Delete that pool file, `private/manifest.txt`, and the test submission at the
   provider, so the real pool starts empty and the manifest carries no trace of
   the probe.

## Hand back

Give them two links: the hosted `dist/interview.md` and the form URL. Circulate
`dist/trust-brief.md` alongside. Say which protections are
real — no name, no email, no login anywhere on the form — and which are
best-effort: a respondent's own LLM account may retain the conversation under its
own policy, and on a Google Form three settings depend on nobody changing them
later. Don't round that up to "anonymous, full stop."

## What you never do

- Hand-edit anything under `dist/`. Edit the source and recompile.
- Weaken the `private/` entry in `.gitignore`.
- Add a second field to the form "just for context." One input block only.
- Set `uniqueSubmissionKey`. Deduplicating by respondent is identity tracking
  under another name.
