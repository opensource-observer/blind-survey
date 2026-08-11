# ingest — pull submissions without pulling identity

## Pull, then screen

```bash
uv run python tools/ingest.py                  # the provider configured in survey.yaml
uv run python tools/ingest.py --csv <path>      # a CSV downloaded by hand
uv run python tools/check_pool.py               # run after every pull
```

Each pull writes new files to `private/pool/`, one per submission,
holding answer text only. Run `check_pool.py` right after — it's the
screen that catches what shouldn't be there before anyone reads the pool
for analysis.

## The rule: form creation may go through MCP; submissions never do

`/setup` may create a Tally form through its MCP server. Pulling
submissions never goes through MCP, or through any other conversational
tool — only `tools/ingest.py`, called directly.

The reason is what a submission carries, not what it says. A Tally
submission carries `respondentId`, `createdAt`, `pdfUrl`, and
`previewUrl` alongside the answer text. A Google Forms response carries
`responseId`, `createTime`, and `lastSubmittedTime`. None of that is
anything a respondent wrote — it's metadata that ties timing and a stable
per-respondent handle to content. Pulling it through a conversational
tool puts all of it in an agent's context, where it persists for the life
of that context and can be correlated against anything else said there.
`tools/ingest.py` reads those fields in memory, uses them only to
deduplicate against `private/manifest.txt`, and writes nothing but the
answer text to the pool. That guarantee only holds if the script is the
thing touching the API — never hand a submissions endpoint to an agent
directly, no matter how convenient the MCP connection already sitting
there looks.

## A check_pool.py hit

```bash
uv run python tools/check_pool.py --strict   # for CI; exits 1 on any hit
```

A hit is a prompt to look, not a verdict. Open the flagged file, read the
line it pointed at, and decide: a leaked provider column or a pasted
`respondentId` should come out by hand; an email or a date usually means
a respondent pasted more than the block and the whole file needs a look;
a link is not automatically wrong on its own — a legitimate statement can
mention one. Edit the pool file directly when something needs to be
removed. There's no undo beyond care, since `private/` is gitignored on
purpose — read before you delete.

## What this does not do

The guarantee this pipeline makes is that provider metadata never reaches
disk — the fields above, none of which a respondent typed. It does not
scrub identity-shaped text a respondent types into their own answer. If
someone writes their own name, or pastes something that reads like an
ID, into the contribution block itself, `tools/ingest.py` carries it
through faithfully, because from the tool's point of view that text is
just the answer. `tools/check_pool.py` is the advisory mitigation for
exactly this: it screens the pool for emails, dates, and links after the
fact. It is not a guarantee, and a hit is not automatically a violation —
see `/administer` for what to do about one.

## The CSV is deleted every time

Whether it came from a Google Forms export or a manual Tally download,
the CSV file is deleted after every ingest, without exception. It is the
one artifact anywhere in this pipeline that ties submission timing to
submission content on the same line of the same file. The pool and the
manifest are kept deliberately apart for that reason; don't let a
downloaded CSV sitting on disk undo it.
