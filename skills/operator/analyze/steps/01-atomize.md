# Step 1 — atomize

Turn raw pool contributions into one statement per bullet. Run this in a fresh
session that has read nothing about this survey except what this file tells it
to read.

## Read first, in this order

1. `rules/statement-style.md` — what a statement is allowed to look like.
2. `rules/anonymity.md` — the identifiability check you apply before flagging.
3. `schema/statement.md` — the exact keys a statement record may carry.
4. `survey.yaml` — the facet lists you are resolving into, and nothing outside
   those lists is a valid value.

## Inputs

`private/pool/*.txt`, and nothing else. Every pool file, every one of them, and
no other file in this repository. Do not open `private/manifest.txt` — it holds
submission ids and is out of scope for this step by design.

## Outputs

- `private/work/statements.jsonl`
- `private/work/term-usage.yaml`
- `private/work/flags.md`
- `private/work/01-notes.md`

## Procedure

1. Read every pool file. Strip the block header and any blank lines; what
   remains is a set of `- ` bullets. If a file holds prose outside a bullet,
   treat each paragraph of that prose as one statement, and record it as a
   format deviation in `01-notes.md` — do not silently fold it into a
   neighboring bullet.
2. Record nothing about where a bullet came from: no filename, no index, no
   position in the file, no grouping of any kind. Step 2 shuffles the list it
   receives; your job is to make that shuffle irreversible, not merely
   inconvenient to undo.
3. One statement per bullet. Never split one bullet into two statements, and
   never merge two bullets into one. If a bullet packs two claims together
   ("funding is tight, and that is why the security review slipped" is one
   bullet holding two assertions), it still becomes exactly one statement —
   note the packing in `01-notes.md` rather than resolving it by splitting.
   Derive every facet from the bullet's **primary assertion**, not from a
   trailing explanatory clause. A bullet that reads "funding follows visible
   releases, because that is what boards can see" is about funding, not about
   boards — label it `scope: funding`, not `scope: governance`. Labeling off
   the explanation rather than the claim is the single most common way two
   bullets that actually contradict each other end up filed under different
   facets and never meet in step 2.
4. `statement` is the bullet with its confidence preamble removed, left in the
   respondent's own wording. Do not improve the prose, add a specific you were
   not given, generalize a detail away, or translate an ambiguous word into
   whatever you privately think it means.
5. `confidence` comes from the stock phrasing and nothing else: "I'm confident
   that" maps to `high`, "I believe" maps to `medium`, "My hunch is" maps to
   `low`. If a bullet hedges in its own words instead of the stock phrasing —
   "I'd bet that…", "I suspect…", "I'm pretty sure…" — map it to the nearest
   tier by what the hedge itself communicates, and record the mapping you chose
   in `01-notes.md`. Never set confidence by how dramatic or forceful the
   content is; a flatly stated small claim and a hedged large one keep whatever
   tier their own opening words carry.
6. Every facet declared in `survey.yaml` gets a value from that facet's own
   list, resolved from the bullet's own words only. When a bullet uses a bare,
   ambiguous term and does not itself resolve it, the value is `unspecified` —
   never resolved from another bullet, from which file the bullet arrived in,
   or from what most bullets in the pool seem to mean by that term. Two
   bullets that both say "users" may land on two different values, or one may
   land on `unspecified` while the other resolves cleanly. That divergence is
   not an error to fix; it is the correct, honest output.
7. Whenever a bullet's resolution of an ambiguous term turns on how the bullet
   uses that term, record it in `term-usage.yaml`: the term itself, the phrase
   that did or did not resolve it, the facet value you assigned, and
   `defines: true` where the bullet states outright what the term means for
   that respondent.
8. For every statement, ask whether its substance — not its wording, its
   substance — could point at who wrote it, at this group's size. A number,
   role, or responsibility only one person plausibly holds is a yes. Where it
   is, append one line to `flags.md` explaining why, and leave the statement in
   `statements.jsonl` exactly as drafted. Flag; never edit, soften, or drop a
   statement on your own authority — that decision belongs to step 2's
   carry-forward and, ultimately, to the operator.
9. Write no count anywhere, including in `01-notes.md`. If you need to know how
   many bullets, statements, or files there were in order to make a judgment
   call, use that number in your head and do not write it down anywhere, not
   spelled out and not in digits.

## Worked example

Input, one pool file:

```text
SURVEY CONTRIBUTION
- I'm confident that our users are the operators running this in production, not the people building on top of our API
- I believe users mostly want new capabilities and tolerate breakage to get them
- I'm confident that the same three people review every pull request, and that number has not grown in years
- My hunch is that our finance lead is the only person who has ever seen the full infrastructure budget broken down by project
```

`statements.jsonl` it produces — four lines, in no particular order, none of
them carrying anything about which file or position they came from:

```jsonl
{"statement": "Our users are the operators running this in production, not the people building on top of our API", "confidence": "high", "kind": "belief", "role": "user", "scope": "tooling"}
{"statement": "Users mostly want new capabilities and tolerate breakage to get them", "confidence": "medium", "kind": "belief", "role": "unspecified", "scope": "tooling"}
{"statement": "The same three people review every pull request, and that number has not grown in years", "confidence": "high", "kind": "risk", "role": "maintainer", "scope": "community"}
{"statement": "Our finance lead is the only person who has ever seen the full infrastructure budget broken down by project", "confidence": "low", "kind": "observation", "role": "maintainer", "scope": "funding"}
```

The first two bullets both use the bare word "users" and land on different
values, exactly as the procedure allows: the first bullet defines what it
means by "users" in its own words, so `role` resolves to `user`; the second
never resolves the word on its own, so `role` stays `unspecified`. That is
recorded in `term-usage.yaml`:

```yaml
- term: users
  phrase: "our users are the operators running this in production, not the people building on top of our API"
  value: user
  defines: true
- term: users
  phrase: "users mostly want new capabilities and tolerate breakage to get them"
  value: unspecified
  defines: false
```

The fourth statement names a single function — whoever leads finance — holding
a specific number nobody else has seen. That goes into `flags.md`, unchanged
in `statements.jsonl`:

```markdown
- Statement 4 ("Our finance lead is the only person who has ever seen the full
  infrastructure budget broken down by project"): names a single-function role
  holding a specific figure only that person could have seen. At this group's
  size, the substance points at them even though no name appears.
```

## Done when

- [ ] Every bullet in every pool file produced exactly one statement — no
      splitting, no merging.
- [ ] No statement carries a key outside `statement`, `confidence`, and the
      facets declared in `survey.yaml`.
- [ ] Nothing in any output file identifies which statements arrived together
      — no filename, no index, no ordering, no grouping.
- [ ] Every bare, ambiguous referent a bullet did not itself resolve is
      `unspecified`, never guessed from elsewhere.
- [ ] `uv run python tools/validate.py private/work/statements.jsonl` reports
      clean.
- [ ] No output states a count anywhere, spelled out or in digits.
