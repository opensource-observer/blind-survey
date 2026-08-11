# administer — field the survey and keep the channel honest

## Distribute together, never separately

Hand out the interview prompt (`dist/interview.md`, wherever it's hosted)
and the form URL in the same message, every time. A prompt with no form
has nowhere for its output to go. A form with no prompt invites someone
to type straight into the box, off script and without the sign-off step
that makes this design work. Never split the two across separate
messages or separate channels.

## Answer process questions, not content questions

Respondents and the program manager will ask how this works — what
happens to a submission, how the anonymity holds up, when the form
closes. Answer all of that freely. Never ask about, comment on, or repeat
what anyone actually said. You have no reason to be reading the pool
during administration, and shouldn't act as if you are.

## Re-verify before every pull

Before each `/ingest` run, run:

```bash
uv run python tools/verify_form.py
```

again, even though `/setup` already ran it once. On a Google Form, three
settings — requiring sign-in, a one-response-per-person cap, and response
editing — are invisible to the API and can be switched on in the UI after
the form was created and originally verified. This check is the only
thing standing between that and nobody noticing before the next pull. Run
it before each pull, not just the first one.

## The two failure modes

**A respondent pastes their whole transcript**, not the approved block
alone. The pool file will hold far more than a short statement list,
including content the respondent may never have meant to release outside
the conversation. Don't wave it through: read it, recover only what maps
to statements they visibly approved if that's possible, and otherwise
flag the file for a human decision rather than running it into analysis
untouched.

**A respondent pastes their own name**, or another identifying detail,
into the block itself. `tools/check_pool.py` will not catch a bare name —
it screens for emails, dates, and links, not proper nouns generally — so
this is caught by reading, not by tooling. Redact it by hand in the pool
file before that statement goes anywhere near analysis.

Both cases mean opening a pool file and editing it directly, which is
fine: the anonymity design blinds who submitted, not the operator's
ability to fix a mistake sitting in the text.

## Closing the form

When the survey period ends: close the form at the provider — set it
closed or unpublish it on Tally, turn off accepting responses on Google
Forms — then delete `private/manifest.txt` and any downloaded CSV export
still sitting on disk. The manifest and a CSV export are the only
artifacts anywhere in this pipeline that tie submission timing to
content. Once the form is closed, keeping either buys nothing and only
adds a leak surface.

## The paper fallback

If `submission.provider` is `paper`, there is no API to verify or pull
from. Administering it by hand means:

1. Type each response sheet into its own pool file, verbatim.
2. Number new files starting one past the highest number already present
   in `private/pool/` — never reuse or renumber an existing file.
3. Before typing a sheet in, grep the pool for a distinctive phrase from
   it. A hit means that sheet is a duplicate of one you already typed,
   not a new submission — skip it rather than adding it again.
4. Shred the sheet once it's typed in and checked against the pool.
   Paper is the only channel with no metadata at all; don't let the
   sheet itself become the record that undoes that.
