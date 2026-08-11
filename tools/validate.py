"""Lint statements.jsonl against the schema and the style rules.

The interview asks for these properties; this checks them. Run it before any
statement file is analyzed or handed on.

Usage:  uv run python tools/validate.py private/work/statements.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# `uv run python tools/validate.py` — the documented command, since the
# audience for this repo cannot be asked to know about `-m` — only puts this
# file's own directory on sys.path, not the repo root. The absolute
# `tools.config` import below would fail without this. pytest gets away
# without it because pyproject.toml sets pythonpath = ["."].
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.config import CONFIDENCE_TIERS, Survey, load_survey  # noqa: E402

MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|"
    "November|December"
)
TEXT_SCREENS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("date", re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "holds a date"),
    ("year", re.compile(r"\b(?:19|20)\d{2}\b"), "holds a bare year"),
    (
        "time",
        re.compile(
            r"\b(?:next|last|this|past|coming)\s+"
            r"(?:year|quarter|month|week|cycle|season)\b"
            rf"|\bsince\s+(?:{MONTHS})\b"
            r"|\bQ[1-4]\b",
            re.IGNORECASE,
        ),
        "points at a relative time",
    ),
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}"), "holds an email address"),
    ("link", re.compile(r"https?://|\bwww\.", re.IGNORECASE), "holds a link"),
    ("handle", re.compile(r"(?<![\w.])@\w{2,}"), "holds an @handle"),
)


@dataclass(frozen=True)
class Finding:
    line: int
    field: str
    message: str


def _screen_text(
    text: str, line: int, survey: Survey, field: str = "statement"
) -> list[Finding]:
    out = [
        Finding(line, field, f"{field} {why}: {pattern.search(text).group(0)!r}")
        for _name, pattern, why in TEXT_SCREENS
        if pattern.search(text)
    ]
    for word in survey.stoplist:
        if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
            out.append(
                Finding(line, field, f"{field} holds stoplist word {word!r}")
            )
    return out


def check_record(record: dict, line: int, survey: Survey) -> list[Finding]:
    out: list[Finding] = []

    text = record.get("statement")
    if text is None:
        out.append(Finding(line, "statement", "missing required key 'statement'"))
    elif not isinstance(text, str) or not text.strip():
        out.append(Finding(line, "statement", "'statement' is empty"))
    else:
        out.extend(_screen_text(text, line, survey))

    confidence = record.get("confidence")
    if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
        out.append(
            Finding(line, "confidence", "confidence is numeric; use high, medium or low")
        )
    elif confidence not in CONFIDENCE_TIERS:
        out.append(
            Finding(
                line,
                "confidence",
                f"confidence {confidence!r} is not one of {', '.join(CONFIDENCE_TIERS)}",
            )
        )

    for facet, allowed in survey.facets.items():
        if facet not in record:
            out.append(Finding(line, facet, f"missing declared facet {facet!r}"))
        elif record[facet] not in allowed:
            out.append(
                Finding(
                    line,
                    facet,
                    f"{facet} {record[facet]!r} is not in its declared list",
                )
            )

    # `submission` is not a supported field, so the loop below reports it as an
    # undeclared key like any other. A hand-edited file that carries one still
    # gets its content screened, because the text screens are the point.
    submission = record.get("submission")
    if isinstance(submission, str) and submission.strip():
        out.extend(_screen_text(submission, line, survey, field="submission"))

    for key in record:
        if key not in survey.statement_keys:
            out.append(Finding(line, key, f"undeclared key {key!r}"))

    return out


def check_all(records: list[dict], survey: Survey) -> list[Finding]:
    out: list[Finding] = []
    for index, record in enumerate(records, 1):
        out.extend(check_record(record, index, survey))
    return out


def load_jsonl(path: Path) -> list[dict]:
    records = []
    for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{index}: not valid JSON — {exc}") from exc
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("statements", type=Path, help="path to statements.jsonl")
    parser.add_argument("--survey", type=Path, default=None)
    args = parser.parse_args(argv)

    survey = load_survey(args.survey)
    findings = check_all(load_jsonl(args.statements), survey)
    if not findings:
        print(f"{args.statements}: clean")
        return 0
    for finding in findings:
        print(f"line {finding.line} · {finding.field}: {finding.message}")
    print(f"\n{len(findings)} problem(s). Nothing here is safe to hand on yet.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
