"""Describe how much material supports a view, without naming anyone.

The unit here is statements, never people. A statement record carries no field
naming whoever wrote it, deliberately, so this module cannot count people even
in principle. One person who says five things about security fills a cell of
five on their own. That is why `describe()` never hands back a bare number: a
count of statements is not a count of respondents, and printing it as one
would claim precision this pipeline has no way to earn.

`anonymity.min_cell_size` marks the point below which there is too little
material to call something a theme. It is not a k-anonymity control — it never
was one, because five statements standing for one person are just as thin as
five statements standing for five. Below that line, the honest answer is
"limited evidence"; at or above it, the phrase comes from the cell's share of
the total instead.

The vocabulary is the five phrases in `rules/quantifiers.md`. One of them,
"contested across the material", is a judgment call this module never makes
on its own; a person reading the material chooses it, the way the phrase
below could not know that two of a cell's five statements retract the other
three.

The only honest bound on how many *people* a cell could represent is the
number of submissions the pool holds — one pool file is one submission, with
no statement-level linkage to it. `main()` prints that count whenever the pool
directory is available, and labels every number as statements so a reader
cannot mistake either figure for a headcount.

Usage:  uv run python tools/breadth.py private/work/statements.jsonl subject_role --pool private/pool
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

from tools.config import QUANTIFIERS, ROOT, Survey, load_survey  # noqa: E402

# Bound from the canonical tuple, not local literals, so a wording change in
# tools/config.py (and rules/quantifiers.md) cannot silently desynchronize
# this module from it. Unpacking by position also fails loudly at import
# time if the tuple's length ever changes. The judgment-call phrase is named
# so it is visible that this module never returns it on its own.
RECURRING, APPEARS, LIMITED, SINGLE, _CONTESTED = QUANTIFIERS


def describe(count: int, total: int, survey: Survey) -> str:
    if count < 1:
        raise ValueError("nothing to describe: count is zero")
    if count > total:
        raise ValueError(f"count {count} is more than the total {total}")

    if count == 1:
        return SINGLE

    if count < survey.anonymity.min_cell_size:
        return LIMITED

    share = count / total
    if share >= 0.66:
        return RECURRING
    if share >= 0.33:
        return APPEARS
    return LIMITED


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def tally(records: list[dict], facet: str, survey: Survey) -> dict[str, str]:
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
    parser.add_argument(
        "--pool",
        type=Path,
        default=ROOT / "private" / "pool",
        help="submission pool, for the free denominator (default: private/pool)",
    )
    args = parser.parse_args(argv)

    from tools.validate import load_jsonl

    survey = load_survey(args.survey)
    records = load_jsonl(args.statements)
    counts = Counter(r[args.facet] for r in records if args.facet in r)
    breadth = tally(records, args.facet, survey)
    total = sum(counts.values())

    if args.pool.is_dir():
        submissions = len(list(args.pool.glob("*.txt")))
        print(f"{_plural(total, 'statement')} from {_plural(submissions, 'submission')}.")
    else:
        print(f"{_plural(total, 'statement')}.")
    print("A cell of N statements represents at most N people, and possibly one.")
    print()
    for value, count in counts.most_common():
        print(f"  {value}: {_plural(count, 'statement')} — {breadth[value]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
