# Statement schema

A statement is derived from approved text only. Its structure never carries
anything the respondent did not approve.

Two fields are fixed by the protocol:

```yaml
statement: "Downstream users assume a dependency is maintained because it is widely installed"
confidence: medium     # high | medium | low, read from the approved phrasing and nothing else
```

Every other field is a facet declared in `survey.yaml`, and its value must come
from that facet's list. The shipped example declares three:

```yaml
kind: belief           # observation | belief | hypothesis | constraint | asset | risk | question | unspecified
role: maintainer       # maintainer | funder | user | researcher | unspecified
scope: security        # funding | security | governance | tooling | community | unspecified
```

Every facet list carries `unspecified`. When a statement's own words do not
resolve a facet, the value is `unspecified` — never a guess drawn from another
statement, from which file it arrived in, or from what most answers seem to mean.

`statements.jsonl` holds one JSON object per line, with exactly these keys.

Deliberately absent: names, job titles, and free-text descriptions of what a
person does — distinct from the closed `role` facet declared above — dates,
direct quotes, timestamps, submission ids, form row identifiers, arrival order,
source file, hashes, statement ids, and lifecycle states. No field links two
statements to the same interview, and none can be added: the step that writes
these records never learns which contribution a bullet came from.
