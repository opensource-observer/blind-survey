"""Pull submissions and write the answer text, and only the answer text, to the pool.

Every provider hands back more than the answer. Tally carries respondentId,
createdAt, pdfUrl and previewUrl; Google Forms carries responseId, createTime,
lastSubmittedTime and respondentEmail if it was ever collected. All of it is
read here, in memory, to deduplicate — and none of it is written anywhere.

This is also why submissions are never fetched through a conversational tool:
those fields would land in an agent's context, which is a place they persist.

Usage:
  uv run python tools/ingest.py                          # the configured provider
  uv run python tools/ingest.py --csv ~/Downloads/x.csv  # the CSV fallback
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import random
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# `uv run python tools/ingest.py` — the documented command, since the
# audience for this repo cannot be asked to know about `-m` — only puts this
# file's own directory on sys.path, not the repo root. The absolute
# `tools.config` import below would fail without this. pytest gets away
# without it because pyproject.toml sets pythonpath = ["."].
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.config import ROOT, Survey, load_survey  # noqa: E402

POOL = ROOT / "private" / "pool"
MANIFEST = ROOT / "private" / "manifest.txt"


@dataclass(frozen=True)
class Row:
    """One submission, reduced to a deduplication key and the answer text."""

    key: str
    text: str


def _digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_tally(payload: dict, field_label: str) -> list[Row]:
    question_id = next(
        (q["id"] for q in payload.get("questions", []) if q.get("title") == field_label),
        None,
    )
    if not question_id:
        raise ValueError(f"no question titled {field_label!r} on the form")

    rows = []
    for submission in payload.get("submissions", []):
        key = (submission.get("id") or "").strip()
        text = ""
        for response in submission.get("responses", []):
            if response.get("questionId") == question_id:
                text = (response.get("answer") or "").strip()
        if key and text:
            rows.append(Row(key, text))
    return rows


def parse_google(payload: dict, field_label: str, form: dict) -> list[Row]:
    question_id = None
    for item in form.get("items", []):
        if item.get("title") == field_label and "questionItem" in item:
            question_id = item["questionItem"]["question"].get("questionId")
    if not question_id:
        raise ValueError(f"no question titled {field_label!r} on the form")

    rows = []
    for response in payload.get("responses", []):
        answer = (response.get("answers") or {}).get(question_id) or {}
        values = (answer.get("textAnswers") or {}).get("answers") or []
        text = " ".join((v.get("value") or "") for v in values).strip()
        if not text:
            continue
        # Google Forms does expose a submission id (`responseId`) through the
        # API, so key on it when present. Only the CSV export path — handled
        # by parse_csv, not here — genuinely lacks any id, and falls back to
        # a digest of the text there.
        response_id = (response.get("responseId") or "").strip()
        rows.append(Row(response_id or _digest(text), text))
    return rows


def parse_csv(text: str, field_label: str) -> list[Row]:
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for record in reader:
        if field_label not in record:
            raise ValueError(f"no column {field_label!r} — check the form label")
        body = (record.get(field_label) or "").strip()
        if not body:
            continue
        key = ""
        for column in ("Submission ID", "Response ID", "id"):
            if record.get(column):
                key = record[column].strip()
                break
        rows.append(Row(key or _digest(body), body))
    return rows


def write_pool(
    rows: list[Row], pool: Path, manifest: Path, rng: random.Random
) -> list[Path]:
    pool.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)

    seen = set()
    if manifest.exists():
        seen = {
            line.strip()
            for line in manifest.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    fresh: list[Row] = []
    for row in rows:
        digest = _digest(row.key)
        if digest in seen:
            continue
        seen.add(digest)  # also deduplicates repeats inside this one batch
        fresh.append(row)
    if not fresh:
        return []

    start = 1 + max(
        (int(p.stem) for p in pool.glob("*.txt") if p.stem.isdigit()), default=0
    )
    rng.shuffle(fresh)  # arrival order is not evidence

    written = []
    for offset, row in enumerate(fresh, start=start):
        target = pool / f"{offset:03d}.txt"
        if target.exists():
            raise FileExistsError(f"{target} exists — refusing to overwrite")
        target.write_text(row.text.rstrip() + "\n", encoding="utf-8")
        written.append(target)

    # Sorted, not appended. Digesting the key (above) defeats a passive read
    # of the checkout, but appending in write order preserves something a
    # digest alone can't hide: manifest line i and pool file i are still the
    # same submission, in the same relative order, every run. Anyone with
    # live provider access — which the join needs anyway, to turn a
    # submission id into a respondentId and a timestamp — can enumerate
    # candidate ids, hash each one, and pair positions to fully recover the
    # mapping without ever cracking a digest. Digest order carries no
    # relationship to pool order, so writing the manifest sorted removes
    # position as a source of information; pairing line i with pool file i
    # then recovers nothing.
    #
    # This does mean the manifest is rewritten whole on every run instead of
    # only appended to. That's an acceptable trade: the manifest holds no
    # content, only digests, and it's deleted when the form closes — losing
    # append-only-ness costs nothing that anonymity depends on.
    manifest.write_text("".join(digest + "\n" for digest in sorted(seen)), encoding="utf-8")

    return written


def _fetch_tally(form_id: str, key: str, field_label: str) -> list[Row]:
    rows: list[Row] = []
    page = 1
    while True:
        request = urllib.request.Request(
            f"https://api.tally.so/forms/{form_id}/submissions?page={page}",
            headers={
                "Authorization": f"Bearer {key}",
                # Tally's edge rejects the default urllib user agent.
                "User-Agent": "blind-survey/0.1",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
        rows.extend(parse_tally(payload, field_label))
        if not payload.get("hasMore"):
            return rows
        page += 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=None, help="a downloaded CSV export")
    parser.add_argument("--survey", type=Path, default=None)
    parser.add_argument("--pool", type=Path, default=POOL)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args(argv)

    survey = load_survey(args.survey)
    label = survey.submission.field_label

    if args.csv:
        rows = parse_csv(args.csv.read_text(encoding="utf-8"), label)
    elif survey.submission.provider == "tally":
        key = os.environ.get("TALLY_API_KEY", "")
        if not key:
            print("TALLY_API_KEY is not set")
            return 2
        if not survey.submission.form_id:
            print("survey.yaml has no submission.form_id yet")
            return 2
        rows = _fetch_tally(survey.submission.form_id, key, label)
    else:
        print(
            f"provider {survey.submission.provider!r} has no direct fetch path here. "
            "Download the responses and pass --csv, or type paper submissions into "
            "the pool by hand."
        )
        return 2

    written = write_pool(rows, args.pool, args.manifest, random.Random())
    if not written:
        print("nothing new since the last run")
        return 0
    print(f"wrote {len(written)} file(s) to {args.pool}, ending at {written[-1].name}")
    print("now run: uv run python tools/check_pool.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
