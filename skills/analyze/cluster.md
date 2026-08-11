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
   group across two values of the same facet: a `subject_role: maintainer`
   statement and a `subject_role: funder` statement are claims made from
   different positions, even when their wording overlaps.
3. When two statements in a group cannot both be true, that group becomes a
   **disagreement** entry: both positions, in the respondents' own terms, side by
   side. Report it; do not resolve it or declare a majority.
4. Read `term-usage.yaml` for the same term resolved to different facet values.
   Each divergence becomes a **term tension** entry. Where one usage defines the
   term and another contradicts that stated definition, say so rather than
   treating the two as different opinions.
5. For every claim about how much material supports a view, call `breadth.py`
   and quote what it returns verbatim — nothing rounded, softened, or restated:

   ```bash
   uv run python tools/breadth.py private/work/statements.jsonl <facet>
   ```

   It always answers with one of the five phrases in `rules/quantifiers.md`,
   never a bare number standing for people. One of the five is a judgment call
   it never produces on its own: "contested across the material". When that is
   the honest answer, choose it yourself from the rule file and write one line
   in `02-notes.md` saying why.
6. `breadth.py` also prints how many statements went into a cell and, when it
   can find the submission pool, how many submissions came in overall. Quote
   that line into `findings.md` alongside the phrase, so a reader sees the
   ceiling on how many people a cell could represent without anyone computing
   it by hand. Never write a count of your own devising: the only figures that
   belong in `findings.md` are the ones `breadth.py` printed, labeled as
   statements and submissions, never as people.
7. Order `findings.md` so the most contested or most surprising material leads. If
   the top entry is something every respondent already agreed on before the survey
   ran, move it down and reorder.
8. Carry every entry from `flags.md` forward as an explicit decision recorded in
   `findings.md` or `02-notes.md`: either broaden the statement's wording so it no
   longer points at one person, or hand the flag to the operator with a one-line
   reason why it cannot be broadened safely. Every flag gets a decision; none is
   dropped or resolved silently.
