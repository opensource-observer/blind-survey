"""Read a form back from its provider and diff it against the blind spec.

The point is that anonymity stops being a checklist somebody ticked. Every
requirement that the provider's API will report is checked here, and every
requirement it will not report is named in `unverifiable` rather than assumed.

Usage:
  uv run python tools/verify_form.py --from-file tests/fixtures/tally-form-compliant.json
  uv run python tools/verify_form.py            # fetches the configured form
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# `uv run python tools/verify_form.py` — the documented command, since the
# audience for this repo cannot be asked to know about `-m` — only puts this
# file's own directory on sys.path, not the repo root. The absolute
# `tools.config` import below would fail without this. pytest gets away
# without it because pyproject.toml sets pythonpath = ["."].
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.config import Survey, load_survey  # noqa: E402

# Known-benign, purely presentational blocks: they carry no answer and are
# never worth banning. Everything else counts as an input block by default —
# this is an allowlist of what's safe, not a blocklist of what isn't, so the
# next block type Tally ships (a new question type, a new layout block,
# whatever) fails the check instead of slipping past it unnamed. That
# includes, among the types this repo has seen slip through before: a
# dropdown or multiple-choice question's per-option blocks (DROPDOWN_OPTION,
# CHECKBOX, MULTIPLE_CHOICE_OPTION, MULTI_SELECT_OPTION, RANKING_OPTION),
# RESPONDENT_COUNTRY, CALCULATED_FIELDS, and MATRIX_ROW / MATRIX_COLUMN.
TALLY_PRESENTATIONAL_TYPES = (
    "FORM_TITLE",
    "TITLE",
    "TEXT",
    "DIVIDER",
    "IMAGE",
    "PAGE_BREAK",
)
TALLY_FALSY_SETTINGS = (
    ("hasSelfEmailNotifications", "an operator notification would carry the answer text"),
    ("hasRespondentEmailNotifications", "a receipt email needs an address"),
    ("hasPartialSubmissions", "partial submissions give each respondent a durable handle"),
)
GOOGLE_UNVERIFIABLE = (
    "require sign-in: not exposed by the Forms API — and not settable through it either",
    "limit one response per user: not exposed by the Forms API, and it would require sign-in",
    "response editing: not exposed by the Forms API",
)


@dataclass(frozen=True)
class Report:
    violations: tuple[str, ...] = ()
    unverifiable: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.violations


def _normalize_ws(text: str) -> str:
    """Collapse whitespace so a title split across rich-text spans compares
    the same as one written as a single span."""
    return re.sub(r"\s+", " ", text).strip()


def _label_of(form: dict, block: dict) -> str:
    """A Tally question's label lives in the TITLE block sharing its groupUuid."""
    for other in form.get("blocks", []):
        if (
            other.get("groupUuid") == block.get("groupUuid")
            and other.get("type") == "TITLE"
        ):
            schema = other.get("payload", {}).get("safeHTMLSchema") or []
            flat = [part for row in schema for part in row if isinstance(part, str)]
            return " ".join(flat).strip()
    return ""


def verify_tally(form: dict, survey: Survey) -> Report:
    bad: list[str] = []
    blocks = form.get("blocks", [])
    settings = form.get("settings") or {}

    if form.get("status") != "PUBLISHED":
        bad.append(
            f"status is {form.get('status')!r}; a live blind form must be PUBLISHED"
        )
    if settings.get("isClosed"):
        bad.append("isClosed is true — the form is closed to submissions")

    inputs = [b for b in blocks if b.get("type") not in TALLY_PRESENTATIONAL_TYPES]
    for block in inputs:
        if block.get("type") != "TEXTAREA":
            bad.append(f"block type {block.get('type')} is banned on a blind form")

    if len(inputs) != 1:
        bad.append(
            f"the form must hold exactly one input block; it holds {len(inputs)}"
        )

    # Check the contribution field on its own terms, not only when the block
    # count is already right — a form with an extra field still has a label and
    # a required flag worth reporting, and reporting every problem at once beats
    # making the operator fix them one round trip at a time.
    textareas = [b for b in inputs if b.get("type") == "TEXTAREA"]
    if not textareas:
        bad.append("the form has no TEXTAREA block to paste a contribution into")
    for block in textareas:
        if not block.get("payload", {}).get("isRequired"):
            bad.append("the contribution field must be required")
        label = _label_of(form, block)
        if _normalize_ws(label) != _normalize_ws(survey.submission.field_label):
            bad.append(
                f"field label is {label!r}; survey.yaml says "
                f"{survey.submission.field_label!r}"
            )

    for key, why in TALLY_FALSY_SETTINGS:
        if settings.get(key):
            bad.append(f"{key} is on — {why}")
    if settings.get("uniqueSubmissionKey"):
        bad.append(
            "uniqueSubmissionKey is set — deduplicating by respondent is identity "
            "tracking under another name"
        )
    if settings.get("submissionsLimit") is not None:
        bad.append(
            "submissionsLimit is set — a per-person cap would have to know who has "
            "already answered"
        )
    if settings.get("password"):
        bad.append("password is set — a blind form opens for a logged-out stranger")

    return Report(tuple(bad))


def verify_google(form: dict, survey: Survey) -> Report:
    bad: list[str] = []
    settings = form.get("settings") or {}

    collection = settings.get("emailCollectionType")
    if collection != "DO_NOT_COLLECT":
        bad.append(
            f"emailCollectionType is {collection!r}; a blind form needs DO_NOT_COLLECT"
        )

    questions = [item for item in form.get("items", []) if "questionItem" in item]
    if len(questions) != 1:
        bad.append(
            f"the form must hold exactly one question; it holds {len(questions)}"
        )
    if questions:
        question = questions[0]["questionItem"]["question"]
        if not question.get("required"):
            bad.append("the contribution question must be required")
        if not question.get("textQuestion", {}).get("paragraph"):
            bad.append("the contribution question must be a long-answer text question")
        title = questions[0].get("title", "")
        if title != survey.submission.field_label:
            bad.append(
                f"question title is {title!r}; survey.yaml says "
                f"{survey.submission.field_label!r}"
            )

    return Report(tuple(bad), GOOGLE_UNVERIFIABLE)


def verify(form: dict, survey: Survey) -> Report:
    provider = survey.submission.provider
    if provider == "tally":
        return verify_tally(form, survey)
    if provider == "google-forms":
        return verify_google(form, survey)
    return Report(
        (),
        ("paper: there is no provider to query — the box and the shredder are the channel",),
    )


def fetch_tally(form_id: str, key: str) -> dict:
    request = urllib.request.Request(
        f"https://api.tally.so/forms/{form_id}",
        headers={
            "Authorization": f"Bearer {key}",
            # Tally's edge rejects the default urllib user agent.
            "User-Agent": "blind-survey/0.1",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-file", type=Path, default=None)
    parser.add_argument("--survey", type=Path, default=None)
    args = parser.parse_args(argv)

    survey = load_survey(args.survey)
    if args.from_file:
        form = json.loads(args.from_file.read_text(encoding="utf-8"))
    elif survey.submission.provider == "tally":
        key = os.environ.get("TALLY_API_KEY", "")
        if not key:
            print("TALLY_API_KEY is not set")
            return 2
        if not survey.submission.form_id:
            print("survey.yaml has no submission.form_id yet")
            return 2
        form = fetch_tally(survey.submission.form_id, key)
    else:
        print(
            f"provider {survey.submission.provider!r} has no fetch path here; "
            "pass --from-file with the form JSON"
        )
        return 2

    report = verify(form, survey)
    for note in report.unverifiable:
        print(f"cannot check · {note}")
    if report.ok:
        print("\nthe form matches the blind spec on every point the provider reports")
        return 0
    for violation in report.violations:
        print(f"VIOLATION · {violation}")
    print(f"\n{len(report.violations)} violation(s). This form is not blind yet.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
