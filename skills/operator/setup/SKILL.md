# setup — field a survey with no form builder and no terminal

## Who you are talking to

A program manager who wants candid input from a group — grantees, a team,
a cohort — and is not technical. They never open a form builder, write
YAML, or run a command. You do all of that yourself and report back in
plain language: what you did, what you found, what happens next.

## The interview

Ask one question at a time. Wait for an answer before asking the next
one. For every choice ahead of them, say what you would pick and why, in
one sentence, then ask — never hand them a bare menu and make them choose
cold.

Work through these, in order, adapting the wording to how the
conversation actually goes:

1. **Audience and size.** Who is answering, and roughly how many people?
   Get a number even if it's a guess. It decides how breadth gets reported
   later, and it is stated to respondents in both compiled documents, so a
   wild guess is worse than a rough one.
2. **What they want to learn.** What is this survey actually answering,
   and what would change their mind about it? If they can't say what
   would change their mind, the survey is probably scoped too broadly.
3. **What the interviewer should ask.** Propose the questions already in
   `survey.yaml` as a starting point — this checkout ships with a worked
   set for sensing across an open source ecosystem — and let them keep,
   edit, or replace them rather than starting from a blank page.
4. **How long the interview should take.** Recommend the shipped default
   of fifteen minutes unless they push back.
5. **Which provider.** Recommend Tally: its API is free on every plan,
   and every setting the blind spec cares about reads back through it.
   Offer Google Forms only if they need to stay inside a Workspace
   organization, and paper only as a last resort. Tell them up front what
   each choice costs in verification before they pick.

**Recommend, don't survey.** `min_cell_size` follows directly from the
group size from question 1: below about ten people, breadth stays
qualitative no matter what number goes in the field, so say that when you
recommend a value rather than asking them to pick one cold.

## Write survey.yaml

Fill in every key, not only the ones the conversation touched: `name`,
`title`, `audience`, `duration_minutes`, `submission` (`provider`,
`field_label`, `block_header` — leave `form_id` and `form_url` null for
now), `anonymity` (`expected_respondents`, `min_cell_size`), `questions`,
`facets`, `stoplist`.

Every list under `facets` needs `unspecified` — the loader rejects one
that doesn't, because an ambiguous statement should never get resolved by
guessing. Seed `stoplist` with the organization's own name if they gave
you one; it's the first proper noun a statement should never carry.

Hand-editing `survey.yaml` afterwards is fine. This step just gets it
right the first time so nothing downstream has to be redone for a typo.

## Compile

Run:

```bash
uv run python build/compile.py
```

This writes `dist/interview.md`, the prompt a respondent will actually be
handed, and `dist/trust-brief.md`, what they should be told before they
start. Read `dist/interview.md` yourself before it goes anywhere. A
marker that failed to resolve would already have stopped the build —
wording that's simply wrong for this audience will not.

## Create the form

**Tally.** Prefer the MCP server at `https://api.tally.so/mcp` if it's
connected — `claude mcp add tally --transport http https://api.tally.so/mcp`
adds it, over HTTP with OAuth or a bearer key. It's in beta; fall back to
the API directly if it misbehaves. Either way, the form is created with a
`POST` to `https://api.tally.so/forms` (or the MCP equivalent) using
`TALLY_API_KEY` — the API costs nothing on any plan. The form must hold
exactly one input block: a required `TEXTAREA` labeled exactly the value
of `submission.field_label` in `survey.yaml`, with no other input block
and no email or captcha block anywhere on the form. Set
`hasSelfEmailNotifications: false`, `hasRespondentEmailNotifications:
false`, `hasPartialSubmissions: false`; leave `uniqueSubmissionKey` and
`submissionsLimit` unset; leave `password: null`; publish it so
`status: PUBLISHED`.

**Google Forms.** The Forms API's `FormSettings` carries only
`quizSettings` and `emailCollectionType` — set `emailCollectionType:
DO_NOT_COLLECT` and add one required paragraph question. Requiring
sign-in, capping one response per person, and allowing response editing
are absent from the API entirely, in both directions, which also means a
form built through the API cannot come out of it with any of them turned
on. Standing up a GCP project and OAuth client to call that API is not
reasonable to ask of this program manager, so the practical path is a
pre-configured template form they copy in Drive — a copy inherits its
settings — followed by a short checklist you walk them through by hand in
the UI: confirm sign-in is off, confirm there is no per-response limit,
confirm editing is off.

Whichever provider, write the resulting `form_id` and `form_url` back
into `survey.yaml` once the form exists.

## Verify

Run:

```bash
uv run python tools/verify_form.py
```

Any violation it reports stops setup here — fix the form, don't argue
with the tool. It also prints lines starting `cannot check`: read those
aloud to the program manager rather than skipping past them. On a Google
Form there will be three, for sign-in, the per-response limit, and
editing, because the API cannot see any of them — which is exactly why
`/administer` re-runs this same check before every pull.

## Probe end to end

Before this goes near a real respondent, be one yourself:

1. Submit a throwaway block through the live form, the way a respondent
   would.
2. Ingest it: `uv run python tools/ingest.py`.
3. Open the pool file it wrote and confirm it holds exactly the block you
   pasted, and nothing else.
4. Delete that pool file, delete `private/manifest.txt`, and delete the
   test submission at the provider, so the real pool starts empty and the
   manifest carries no trace of your probe.

## Hand back

Give the program manager two links: where `dist/interview.md` is hosted
for respondents, and the form URL. Circulate `dist/trust-brief.md`
alongside them. Say plainly which protections are real — no name, no
email, no login anywhere on the form — and which are best-effort: a
respondent's own LLM account may retain the conversation under its own
policy, and on a Google Form three settings depend on nobody changing
them later. Don't round any of that up to "anonymous, full stop."

## What you never do

- Hand-edit anything under `dist/`. It's generated; edit the source and
  recompile.
- Weaken the `private/` entry in `.gitignore`. That entry is part of the
  anonymity design, not housekeeping.
- Add a second field to the form "just for context." One input block is
  the entire point of the blind spec.
- Set `uniqueSubmissionKey`. Deduplicating by respondent is identity
  tracking under another name, whatever it's called in the settings
  panel.
