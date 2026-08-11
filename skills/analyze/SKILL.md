# analyze — pool to statements

Two steps. **Run each in a fresh session**, handing it only the files its own
prompt names and letting it read them off disk. A session that has read the pool
retains which statements arrived together, so it can partly reconstruct who said
what however the list is ordered later. Only the files on disk cross between the
two sessions.

1. **Atomize** (`atomize.md`) — pool bullets become statements, from
   approved text only.
2. **Cluster** (`cluster.md`) — group what matches, surface what
   conflicts, write the findings.

Between the two, and again at the end:

```bash
uv run python tools/validate.py private/work/statements.jsonl
```

Any finding is a stop. Fix the statement file, not the linter.

## Never write a count by hand

Not in the findings, not in the run notes, not in a comment. Ask `breadth.py`:

```bash
uv run python tools/breadth.py private/work/statements.jsonl subject_role
```

It always answers with one of the five phrases from `rules/quantifiers.md`,
never a bare number standing for people — and it prints the statement count and,
where the submission pool is reachable, the submission count alongside. One of
the five is a judgment call it never returns on its own — choose that yourself,
from the rule file.

## Before anything is shared

- [ ] Both steps ran in fresh sessions, each given only its own named inputs.
- [ ] `validate.py` is clean.
- [ ] Nothing states a count that did not come from `breadth.py`'s own output.
- [ ] Every breadth phrase in `findings.md` is quoted from `breadth.py` verbatim,
      with the statement and submission counts it printed alongside it — it
      counts statements, not people, and the submission count is the only
      honest bound on how many people a cell could represent.
- [ ] No entry's substance points at who said it.
- [ ] Every disagreement is framed as positions, not people.
- [ ] The findings lead with something contested or surprising.
- [ ] The findings read as plain language someone would say aloud in a meeting.
