"""Screen the pool for anything that should not have survived ingest.

Advisory by design. A hit needs a look, not a panic: it may be a leaked provider
column, someone who pasted more than their block, or a perfectly legitimate
statement that happens to mention a link. Read the file and decide.

This screens the pool only. The manifest holds submission ids on purpose and
would light this up on every run, which is why it lives outside the pool.

Usage:
  uv run python tools/check_pool.py
  uv run python tools/check_pool.py --strict   # exit 1 on any hit, for CI
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# `uv run python tools/check_pool.py` — the documented command, since the
# audience for this repo cannot be asked to know about `-m` — only puts this
# file's own directory on sys.path, not the repo root. The absolute
# `tools.config` import below would fail without this. pytest gets away
# without it because pyproject.toml sets pythonpath = ["."].
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.config import ROOT  # noqa: E402

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "provider field",
        # The bare `resp_` and `sub_` anchors also fire on ordinary snake_case
        # prose — "sub_teams", "resp_rate" — not just provider ids. Accepted:
        # this tool is advisory, and a false hit just costs one look.
        re.compile(
            r"\b(?:submission|respondent)[\s_-]*id\b|\bresp_|\bsub_|previewUrl|pdfUrl",
            re.IGNORECASE,
        ),
    ),
    ("date", re.compile(r"\b\d{4}-\d{2}-\d{2}\b")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")),
    ("link", re.compile(r"https?://|\bwww\.", re.IGNORECASE)),
)


@dataclass(frozen=True)
class Hit:
    path: Path
    pattern: str
    line: str


def screen(pool: Path) -> list[Hit]:
    hits: list[Hit] = []
    if not pool.exists():
        return hits
    for path in sorted(pool.glob("*.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            for name, pattern in PATTERNS:
                if pattern.search(line):
                    hits.append(Hit(path, name, line.strip()))
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool", type=Path, default=ROOT / "private" / "pool")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    if not args.pool.exists():
        print(f"{args.pool}: no such directory")
        return 2

    hits = screen(args.pool)
    if not hits:
        print(f"{args.pool}: clean")
        return 0
    for hit in hits:
        print(f"{hit.path.name} · {hit.pattern}: {hit.line}")
    print(
        f"\n{len(hits)} thing(s) to look at. Read each file and decide — some of "
        "these are legitimate."
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
