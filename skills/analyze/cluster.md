# Step 2 — cluster

Turn the atomized statement list into findings: agreements, contradictions, and
words that mean different things to different people. Run this in a fresh session
that has read nothing about this survey except the files below.

## Inputs

- `private/work/statements.jsonl`
- `private/work/term-usage.yaml`
- `private/work/flags.md`
- `rules/quantifiers.md`
- `survey.yaml`

Never the raw submission files step 1 read. The two steps run in separate
sessions so no session holds both the grouped raw text and the shuffled list.

## Outputs

- `private/work/findings.md`
- `private/work/02-notes.md`

## Procedure

1. Shuffle the statement list before reading it for meaning. Do not process it in
   the order it arrived on disk.
2. Group statements that assert the same thing, however differently worded. Never
   group across two values of the same facet: a `role: maintainer` statement and
   a `role: funder` statement are claims made from different positions, even when
   their wording overlaps.
3. When two statements in a group cannot both be true, that group becomes a
   **disagreement** entry: both positions, in the respondents' own terms, side by
   side. Report it; do not resolve it or declare a majority.
4. Read `term-usage.yaml` for the same term resolved to different facet values.
   Each divergence becomes a **term tension** entry. Where one usage defines the
   term and another contradicts that stated definition, say so rather than
   treating the two as different opinions.
5. For every claim about how many people hold a view, call `breadth.py` and quote
   what it returns verbatim — nothing rounded, softened, or restated:

   ```bash
   uv run python tools/breadth.py private/work/statements.jsonl <facet>
   ```

   It answers with an integer or one of the six phrases in `rules/quantifiers.md`.
   Two of the six are judgment calls it never produces on its own: "an isolated
   but strategically important view" and "contested — no side holds more of the
   room". When one of those is the honest answer, choose it yourself from the rule
   file and write one line in `02-notes.md` saying why.
6. Quoting an integer is not the same as publishing it. `breadth.py` counts
   statements, and nothing in a record says whether five statements came from five
   people or from one person with five things to say. Before an integer goes into
   `findings.md`, compare it against how many submissions came in: a figure at or
   near that number counts statements, not people, and a smaller cell can still be
   one person returning to the same subject. Where it could be, write one of the
   six phrases instead and note in `02-notes.md` why the figure was dropped. If
   you were not told how many submissions came in, ask before publishing any
   figure — and judge with that number without writing it down.
7. Order `findings.md` so the most contested or most surprising material leads. If
   the top entry is something every respondent already agreed on before the survey
   ran, move it down and reorder.
8. Carry every entry from `flags.md` forward as an explicit decision recorded in
   `findings.md` or `02-notes.md`: either broaden the statement's wording so it no
   longer points at one person, or hand the flag to the operator with a one-line
   reason why it cannot be broadened safely. Every flag gets a decision; none is
   dropped or resolved silently.
