## Rules: reporting breadth

How much material supports something is reported in words, not numbers.

The vocabulary is these five phrases and nothing else:

- a recurring theme
- appears more than once
- limited evidence
- a single statement
- contested across the material

The unit is statements, not people. Nothing in a statement says who wrote it,
and that link is destroyed on purpose, before anything is labeled — so no
amount of careful counting can recover it, and the tool cannot count people
even in principle. One person who says five things about security fills a
cell of five on their own; a bare figure would report that as five people,
which is not a rounding error, it is a different claim. So no tool here ever
emits a count of statements as if it meant a count of respondents.
`tools/breadth.py` applies that logic; call it rather than deciding by eye.

Below the configured minimum cell size, there is too little material to call
something a theme, and the phrase is "limited evidence". At or above it, the
phrase comes from the cell's share of the total. This threshold never
protected anyone's identity — five statements are just as thin a claim about
five people whether they came from five people or from one — it only marks
where there is enough material to describe a pattern at all.

The one honest bound on how many people a cell could represent is the number
of submissions the pool holds, because one pool file is one submission with no
statement-level link back to it. Say how many submissions came in alongside
any breadth phrase, so a reader can see the ceiling for themselves instead of
inferring a headcount from a statement count.

One of the five is a judgment call no tool can make: "contested across the
material" is chosen by a person reading it, not computed from a share.

Breadth describes how much material supports a claim, so it attaches only
where respondents' own statements stand behind a line. Something taken from a
document carries whatever that document hedges to, and no breadth at all:
writing "a recurring theme" onto a document's claim invents support that was
never given.
