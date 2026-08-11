# Step 2 — cluster

Turn the atomized statement list into findings: what people agree on, what
they contradict each other on, and where the same word turns out to mean
different things to different people. Run this in a fresh session that has
read nothing about this survey except what this file tells it to read.

## Inputs

- `private/work/statements.jsonl`
- `private/work/term-usage.yaml`
- `private/work/flags.md`
- `rules/quantifiers.md`
- `survey.yaml`

Never the raw submission files step 1 read. This step exists to see the
statements with no memory of which ones arrived together, and opening the
pool that step 1 read would defeat that on the spot — the two steps run in
separate sessions precisely so that no single session ever holds both the
grouped raw text and the shuffled statement list at once.

## Outputs

- `private/work/findings.md`
- `private/work/02-notes.md`

## Procedure

1. Before reading the statement list for meaning, shuffle it. Do not process
   it in the order it arrived on disk.
2. Group statements that assert the same thing, however differently worded.
   Never group across two different values of the same facet — a statement
   about `role: maintainer` and a statement about `role: funder` are two
   different statements even if their wording overlaps, because they are
   claims made from two different positions.
3. When two statements in the same group cannot both be true, that group
   becomes a **disagreement** entry: both positions, stated in the
   respondents' own terms, side by side. A disagreement is a finding to report,
   not a conflict to resolve or a majority to declare.
4. Read `term-usage.yaml` for the same term resolved to different facet values
   across different statements. Each such divergence becomes a **term tension**
   entry. Where one usage explicitly defines the term and another usage
   contradicts that stated definition, say so plainly rather than treating the
   two as simply different opinions.
5. For every claim about how many people hold a view, call `breadth.py` and
   quote what it returns, verbatim, with nothing rounded, softened, or
   restated as a different phrase:

   ```bash
   uv run python tools/breadth.py private/work/statements.jsonl <facet>
   ```

   `breadth.py` answers with either an integer or one of the six phrases in
   `rules/quantifiers.md`. Two of those six are judgment calls the tool will
   never produce on its own — "an isolated but strategically important view"
   and "contested — no side holds more of the room". When the honest answer
   is one of those two, choose it yourself, from the rule file, and write one
   line in `02-notes.md` explaining why you chose it over the plainer
   alternative the tool gave you.

   Quoting an integer verbatim is not the same as publishing it. `breadth.py`
   counts statements, and nothing in a statement record tells it whether five
   statements came from five people or from one person with five things to say
   about one topic. So before an integer goes into `findings.md`, compare it
   against how many submissions the survey received. A figure at or near that
   number is a count of statements, not of people, and a smaller cell can still
   be one person who kept returning to the same subject. Where it could be,
   write one of the six phrases instead and say in `02-notes.md` why the figure
   was dropped. If you were not told how many submissions came in, ask for that
   number before publishing any figure — and use it to judge without writing it
   down.
6. Order `findings.md` so the most contested or most surprising material leads.
   If the entry at the top is something every respondent already agreed on
   before this survey ran, that is a sign the ordering — not the content — is
   wrong; move it down and reorder.
7. Carry every entry from `flags.md` forward as an explicit decision recorded
   in `findings.md` or `02-notes.md`: either broaden the statement's wording
   so it no longer points at one person, or hand the flag to the operator with
   a one-line reason for why it cannot be broadened safely. Every flag gets a
   decision. None gets dropped without one, and none gets resolved silently.
