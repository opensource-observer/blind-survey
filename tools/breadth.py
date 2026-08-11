"""Report how many statements sit in a cell, without naming anyone.

A figure is returned only when both the cell and its complement clear
`anonymity.min_cell_size` — five of six clears the threshold itself but names
the one person who differed. Otherwise the answer is one of the six phrases in
`rules/quantifiers.md`.

Two of those six are judgment calls and this module never returns them: "an
isolated but strategically important view" and "contested — no side holds more
of the room" are chosen by a person reading the material.

The unit is statements, not people. A statement record carries no field naming
whoever wrote it, deliberately, so this module cannot count people even in
principle. One person who says five things about security fills a cell of five
on their own, and at a minimum cell size of five that cell comes back as a bare
figure standing for one person. The shipped example shows it: run this over
`examples/oso-ecosystem/statements.jsonl` on `role` and the largest cell is a
figure bigger than the number of submission files in that example's pool.

So a figure out of this module is not publishable on its own. Compare it against
how many submissions the pool holds before it goes into anything anyone reads,
and where a cell could be a few people each saying several things, use a phrase
from `rules/quantifiers.md` instead.

Usage:  uv run python tools/breadth.py private/work/statements.jsonl role
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

# `uv run python tools/breadth.py` — the documented command, since the
# audience for this repo cannot be asked to know about `-m` — only puts this
# file's own directory on sys.path, not the repo root. The absolute
# `tools.config` import below would fail without this. pytest gets away
# without it because pyproject.toml sets pythonpath = ["."].
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.config import QUANTIFIERS, Survey, load_survey  # noqa: E402

# Bound from the canonical tuple, not local literals, so a wording change in
# tools/config.py (and rules/quantifiers.md) cannot silently desynchronize
# this module from it. Unpacking by position also fails loudly at import
# time if the tuple's length ever changes. The two judgment-call phrases are
# named so it is visible that this module never returns them.
BROAD, SEVERAL, MINORITY, _STRATEGIC, ISOLATED, _CONTESTED = QUANTIFIERS


def describe(count: int, total: int, survey: Survey) -> int | str:
    if count < 1:
        raise ValueError("nothing to describe: count is zero")
    if count > total:
        raise ValueError(f"count {count} is more than the total {total}")

    minimum = survey.anonymity.min_cell_size
    complement = total - count
    if count >= minimum and (complement == 0 or complement >= minimum):
        return count

    if count == 1:
        return ISOLATED
    share = count / total
    if share >= 0.66:
        return BROAD
    if share >= 0.33:
        return SEVERAL
    return MINORITY


def tally(records: list[dict], facet: str, survey: Survey) -> dict[str, int | str]:
    if facet not in survey.facets:
        raise ValueError(f"{facet!r} is not a declared facet in survey.yaml")
    counts = Counter(r[facet] for r in records if facet in r)
    total = sum(counts.values())
    return {
        value: describe(count, total, survey)
        for value, count in counts.most_common()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("statements", type=Path)
    parser.add_argument("facet")
    parser.add_argument("--survey", type=Path, default=None)
    args = parser.parse_args(argv)

    from tools.validate import load_jsonl

    survey = load_survey(args.survey)
    for value, breadth in tally(load_jsonl(args.statements), args.facet, survey).items():
        print(f"{value}: {breadth}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
