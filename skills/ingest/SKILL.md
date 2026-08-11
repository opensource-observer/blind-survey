# ingest — pull submissions without pulling identity

## Pull, then screen

```bash
uv run python tools/ingest.py                  # the provider configured in survey.yaml
uv run python tools/ingest.py --csv <path>      # a CSV downloaded by hand
uv run python tools/check_pool.py               # run after every pull
```

Each pull writes new files to `private/pool/`, one per submission, holding answer
text only. Run `check_pool.py` right after, before anyone reads the pool for
analysis.

## Form creation may go through MCP; submissions never do

`/setup` may create a Tally form through its MCP server. Pulling submissions goes
only through `tools/ingest.py`, called directly — never MCP, never any other
conversational tool.

The reason is what a submission carries, not what it says. Alongside the answer
text, a Tally submission carries `respondentId`, `createdAt`, `pdfUrl`, and
`previewUrl`; a Google Forms response carries `responseId`, `createTime`, and
`lastSubmittedTime`. No respondent wrote any of that: it is metadata tying timing
and a stable per-respondent handle to content, and in an agent's context it
persists for the life of that context and can be correlated against anything else
said there. `tools/ingest.py` reads those fields in memory, uses them only to
deduplicate against `private/manifest.txt`, and writes nothing but answer text to
the pool — a guarantee that holds only while the script is the thing touching the
API.

## A check_pool.py hit

```bash
uv run python tools/check_pool.py --strict   # for CI; exits 1 on any hit
```

A hit is a prompt to look, not a verdict. Open the flagged file, read the line it
pointed at, and decide:

- a leaked provider column or a pasted `respondentId` comes out by hand;
- an email or a date usually means a respondent pasted more than the block, so
  read the whole file;
- a link can appear in a legitimate statement.

Edit the pool file directly when something has to go. There is no undo —
`private/` is gitignored — so read before you delete.

## What this does not do

The guarantee is that provider metadata never reaches disk. The pipeline does not
scrub identity-shaped text a respondent types into their own answer: a name, or
something that reads like an ID, inside the contribution block is carried through
faithfully, because to the tool that text is the answer. `tools/check_pool.py` is
the advisory mitigation, screening for emails, dates, and links after the fact. It
is not a guarantee, and a hit is not automatically a violation — see `/administer`.

## The CSV is deleted every time

Whether it came from a Google Forms export or a manual Tally download, the CSV is
deleted after every ingest, without exception. It is the one artifact in this
pipeline that ties submission timing to submission content on the same line of the
same file.
