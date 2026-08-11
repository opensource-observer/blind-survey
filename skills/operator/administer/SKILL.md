# administer — field the survey and keep the channel honest

## Distribute together, never separately

Send the interview prompt (`dist/interview.md`, wherever it's hosted) and the
form URL in the same message, every time. Never split them across messages or
channels: a form with no prompt invites someone to type straight into the box,
off script and without the sign-off step.

## Answer process questions, not content questions

Answer freely when respondents or the program manager ask how this works — what
happens to a submission, how the anonymity holds up, when the form closes. Never
ask about, comment on, or repeat what anyone said. You have no reason to read the
pool during administration.

## Re-verify before every pull

Before each `/ingest` run:

```bash
uv run python tools/verify_form.py
```

Run it before every pull, not just the first. On a Google Form, three settings —
requiring sign-in, a one-response-per-person cap, and response editing — are
invisible to the API and can be switched on in the UI after the form was created
and verified, and this check is the only thing that catches it.

## The two failure modes

**A respondent pastes their whole transcript** instead of the approved block. The
pool file then holds content the respondent may never have meant to release. Read
it, recover only what maps to statements they visibly approved, and otherwise flag
the file for a human decision rather than running it into analysis.

**A respondent pastes their own name**, or another identifying detail, into the
block. `tools/check_pool.py` screens for emails, dates, and links, not proper
nouns, so reading catches this, not tooling. Redact it by hand in the pool file
before that statement goes near analysis.

Both cases mean editing a pool file directly, which is fine: the design blinds
who submitted, not the operator's ability to fix text.

## Closing the form

When the survey period ends, close the form at the provider — set it closed or
unpublish it on Tally, turn off accepting responses on Google Forms — then delete
`private/manifest.txt` and any downloaded CSV export still on disk. They are the
only artifacts here that tie submission timing to content.

## The paper fallback

If `submission.provider` is `paper`, there is no API to verify or pull from:

1. Type each response sheet into its own pool file, verbatim.
2. Number new files starting one past the highest number already in
   `private/pool/`. Never reuse or renumber an existing file.
3. Before typing a sheet in, grep the pool for a distinctive phrase from it. A hit
   means it duplicates a sheet you already typed — skip it.
4. Shred the sheet once it's typed in and checked against the pool.
