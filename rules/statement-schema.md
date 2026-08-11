# Statement schema

A statement comes from approved text only. Its structure carries nothing the
respondent did not approve.

Two fields are fixed by the protocol:

```yaml
statement: "Downstream users assume a dependency is maintained because it is widely installed"
confidence: medium     # high | medium | low, read from the approved phrasing and nothing else
```

Every other field is a facet declared in `survey.yaml`, with its value from that
facet's list. The example declares three:

```yaml
kind: belief           # observation | belief | hypothesis | constraint | asset | risk | question | unspecified
role: maintainer       # maintainer | funder | user | researcher | unspecified
scope: security        # funding | security | governance | tooling | community | unspecified
```

Every facet list carries `unspecified`. When a statement's own words do not
resolve a facet, the value is `unspecified`. Never guess from another statement,
from which file it arrived in, or from what most answers seem to mean.

`statements.jsonl` holds one JSON object per line, with exactly these keys.

Absent, and not addable: names, job titles, free-text descriptions of what a
person does (as distinct from the closed `role` facet above), dates, direct
quotes, timestamps, submission ids, form row identifiers, arrival order, source
file, hashes, statement ids, lifecycle states. No field links two statements to
the same interview: the step that writes these records never learns which
contribution a bullet came from.
