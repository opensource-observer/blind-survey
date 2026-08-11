# Step 1 — atomize

Turn raw pool contributions into one statement per bullet. Run this in a fresh
session that has read nothing about this survey except the files below.

## Read first, in this order

1. `rules/statement-style.md` — what a statement may look like.
2. `rules/anonymity.md` — the identifiability check.
3. `schema/statement.md` — the keys a record may carry.
4. `survey.yaml` — the facet lists. No value outside them is valid.

## Inputs

`private/pool/*.txt` — every pool file, and no other file in this repository.
Do not open `private/manifest.txt`; it holds submission ids.

## Outputs

- `private/work/statements.jsonl`
- `private/work/term-usage.yaml`
- `private/work/flags.md`
- `private/work/01-notes.md`

## Procedure

1. Read every pool file. Strip the block header and blank lines; the rest is `- `
   bullets. Treat prose outside a bullet as one statement per paragraph, and note
   the format deviation in `01-notes.md` rather than folding it into a neighboring
   bullet.
2. Record nothing about where a bullet came from: no filename, index, position,
   or grouping.
3. One statement per bullet. Never split a bullet, never merge two. A bullet
   packing two claims still becomes exactly one statement — note the packing in
   `01-notes.md`.
4. Facets come from the bullet's **primary assertion**, not a trailing
   explanatory clause. "Funding follows visible releases, because that is what
   boards can see" is `scope: funding`, not `scope: governance`.
5. `statement` is the bullet minus its confidence preamble, in the respondent's
   own wording. Do not improve the prose, add a specific you were not given,
   generalize a detail away, or translate an ambiguous word.
6. `confidence` comes from the stock phrasing alone: "I'm confident that" →
   `high`, "I believe" → `medium`, "My hunch is" → `low`. Map an own-words hedge
   ("I suspect…") to the nearest tier and note the mapping in `01-notes.md`.
   Never read confidence off how forceful the content is.
7. Every facet in `survey.yaml` takes a value from its own list, resolved from the
   bullet's own words. A bare, ambiguous term the bullet does not resolve is
   `unspecified` — never resolved from another bullet, from its file, or from what
   most bullets seem to mean. Two bullets that both say "users" may land on
   different values; that divergence is correct output, not an error to fix.
8. Record each ambiguous term in `term-usage.yaml`: the term, the phrase that did
   or did not resolve it, the value you assigned, and `defines: true` where the
   bullet says outright what the term means.
9. Apply `rules/anonymity.md`'s identifiability check to every statement's
   substance, not its wording: a figure, role, or responsibility only one person
   plausibly holds points at who wrote it at this group's size. Where it does,
   append one line to `flags.md` saying why and leave the statement in
   `statements.jsonl` as drafted. Flag; never edit, soften, or drop one yourself
   — that call belongs to step 2's carry-forward and the operator.
10. Write no count anywhere, `01-notes.md` included — not spelled out, not in
    digits. Keep a number a judgment call needs in your head.

## Worked example

Two bullets from one pool file:

```text
SURVEY CONTRIBUTION
- I'm confident that our users are the operators running this in production, not the people building on our API
- I believe users tolerate breakage to get new capabilities
```

Bullet one defines what it means by "users", so its `role` resolves to `user`;
bullet two never resolves the word, so its `role` stays `unspecified`. In
`term-usage.yaml`:

```yaml
- term: users
  phrase: "our users are the operators running this in production"
  value: user
  defines: true
- term: users
  phrase: "users tolerate breakage to get new capabilities"
  value: unspecified
  defines: false
```

## Done when

- [ ] `uv run python tools/validate.py private/work/statements.jsonl` is clean.
- [ ] No statement carries a key outside `statement`, `confidence`, and the
      facets declared in `survey.yaml`.
- [ ] Nothing in any output identifies which statements arrived together — no
      filename, index, ordering, or grouping.
- [ ] No output states a count, spelled out or in digits.
