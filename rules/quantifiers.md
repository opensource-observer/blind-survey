## Rules: reporting breadth

How many people said something is reported in words, not numbers.

The vocabulary is these six phrases and nothing else:

- broad consensus
- several respondents
- a minority view
- an isolated but strategically important view
- an isolated view
- contested — no side holds more of the room

A figure may replace a phrase only when both the group holding the view and the
group not holding it are at least the configured minimum. Five out of six is a
figure that names the one person who differed. `tools/breadth.py` applies that
arithmetic; call it rather than deciding by eye.

Nothing in a statement says who wrote it, so the tool counts entries in a file
and nothing more. The rule is about people: five statements from one person make
a cell of five, which the tool reports as a figure. Check any figure against how
many submissions came in before publishing it. Where the cell could be a few
people each saying several things, use a phrase instead.

Two of the six are judgment calls no tool can make: "an isolated but
strategically important view" and "contested — no side holds more of the room".
A person reading the material chooses those, not a share.

Breadth describes views people hold, so it attaches only where people's answers
stand behind a line. Something taken from a document carries whatever that
document hedges to, and no breadth at all: writing "several respondents" onto a
document's claim invents a room that was never asked.
