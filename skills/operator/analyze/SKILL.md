# analyze — pool to statements

Two steps. **Run each in a fresh session**, handing it only the files its own
prompt names and letting it read them off disk.

That is not hygiene. A session that has read the pool retains which statements
arrived together, so it can partly reconstruct who said what however the list is
ordered afterwards. Two sessions, two sets of named inputs, and the files on disk
are the only thing that crosses between them.

1. **Atomize** (`steps/01-atomize.md`) — pool bullets become statements, from
   approved text only.
2. **Cluster** (`steps/02-cluster.md`) — group what matches, surface what
   conflicts, and write the findings.

Between the two, and again at the end:

```bash
uv run python tools/validate.py private/work/statements.jsonl
```

Any finding is a stop. Fix the statement file, do not fix the linter.

## Never write a count by hand

Not in the findings, not in the run notes, not in a comment. Ask `breadth.py`:

```bash
uv run python tools/breadth.py private/work/statements.jsonl role
```

It returns a number only when a number cannot point at anyone, and one of the
six phrases from `rules/quantifiers.md` otherwise. Two of those six are
judgment calls it will never return — choose those yourself, from the rule file.

## Before anything is shared

- [ ] Both steps ran in fresh sessions, each given only its own named inputs.
- [ ] `validate.py` is clean.
- [ ] Nothing states a count that did not come from `breadth.py`.
- [ ] Every figure `breadth.py` returned was checked against how many
      submissions came in — it counts statements, not people — and any cell that
      could be one person saying several things is written as a phrase.
- [ ] No entry's substance points at who said it.
- [ ] Every disagreement is framed as positions, not people.
- [ ] The findings lead with something contested or surprising. If they don't,
      the analysis has not finished.
- [ ] The findings read as plain language someone would say aloud in a meeting.
