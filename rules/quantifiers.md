## Rules: reporting breadth

How many people said something is reported in words, not numbers, unless the
group is large enough that a figure cannot point at anyone.

The vocabulary is these six phrases and nothing else:

- broad consensus
- several respondents
- a minority view
- an isolated but strategically important view
- an isolated view
- contested — no side holds more of the room

A figure may replace one of them only when both the group holding the view and
the group not holding it are at least as large as the configured minimum. A
group of five out of six is a figure that names the one person who differed.
`tools/breadth.py` applies that arithmetic; call it rather than deciding by eye.

The arithmetic runs over statements, and the rule is about people. Nothing in a
statement says who wrote it, so `tools/breadth.py` counts entries in a file and
cannot do anything else. The two come apart as soon as one person says several
things about the same topic: five statements from one person make a cell of
five, and the tool reports that cell as a figure. Check any figure against how
many submissions came in before publishing it. Where the cell could be a few
people each saying several things, use one of the phrases instead.

Two of the six are judgment calls no tool can make. "An isolated but
strategically important view" and "contested — no side holds more of the room"
are chosen by a person reading the material, not derived from a share.

Breadth describes views people hold, so it attaches only where people's answers
stand behind a line. Something taken from a document carries whatever the
document itself hedges to and no breadth at all. Writing "several respondents"
onto a document's claim invents a room that was never asked.
