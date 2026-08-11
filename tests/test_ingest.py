import hashlib
import json
import random
from pathlib import Path

import pytest

from tools.check_pool import screen
from tools.config import load_survey
from tools.ingest import Row, parse_csv, parse_google, parse_tally, write_pool

SURVEY = load_survey(Path("survey.yaml"))
LABEL = SURVEY.submission.field_label
IDENTITY_MARKERS = ("resp_", "respondentId", "pdfUrl", "previewUrl", "2026-08-09")


def fixture(name: str) -> dict:
    return json.loads(Path(f"tests/fixtures/{name}").read_text(encoding="utf-8"))


def test_parse_tally_returns_only_the_id_and_the_text():
    rows = parse_tally(fixture("tally-submissions.json"), LABEL)
    assert [r.key for r in rows] == ["sub_aaa", "sub_bbb"]
    for row in rows:
        assert row.text.startswith("SURVEY CONTRIBUTION")
        for marker in IDENTITY_MARKERS:
            assert marker not in row.text


def test_parse_tally_skips_blank_answers():
    rows = parse_tally(fixture("tally-submissions.json"), LABEL)
    assert "sub_empty" not in [r.key for r in rows]


def test_parse_tally_fails_loudly_on_a_missing_label():
    with pytest.raises(ValueError, match="no question titled"):
        parse_tally(fixture("tally-submissions.json"), "Some other label")


def test_parse_google_keys_on_the_response_id():
    payload = fixture("google-responses.json")
    rows = parse_google(payload, LABEL, payload["form"])
    assert len(rows) == 1
    assert rows[0].key == "gr_aaa"
    assert rows[0].text.startswith("SURVEY CONTRIBUTION")


def test_parse_google_falls_back_to_a_hash_when_no_id_is_present():
    payload = fixture("google-responses.json")
    del payload["responses"][0]["responseId"]
    rows = parse_google(payload, LABEL, payload["form"])
    assert len(rows) == 1
    assert rows[0].key.startswith("sha256:")


def test_google_response_id_never_reaches_the_pool(tmp_path):
    pool, manifest = tmp_path / "pool", tmp_path / "manifest.txt"
    payload = fixture("google-responses.json")
    rows = parse_google(payload, LABEL, payload["form"])
    written = write_pool(rows, pool, manifest, random.Random(7))
    assert len(written) == 1
    for path in written:
        assert "gr_aaa" not in path.read_text(encoding="utf-8")


def test_parse_csv_handles_multi_line_quoted_answers():
    rows = parse_csv(Path("tests/fixtures/submissions.csv").read_text(encoding="utf-8"), LABEL)
    assert [r.key for r in rows] == ["sub_aaa", "sub_ccc"]
    assert rows[0].text.count("\n") == 1


def test_write_pool_writes_the_text_and_nothing_else(tmp_path):
    # Structural, not marker-based: a hardcoded marker list only catches the
    # specific fields it happens to name, and this fixture's own submission
    # ids (sub_aaa / sub_bbb) don't match any of them. Assert directly that
    # no input key survives into any written file, and cross-check with the
    # advisory pool screen so a leak trips both.
    pool, manifest = tmp_path / "pool", tmp_path / "manifest.txt"
    rows = parse_tally(fixture("tally-submissions.json"), LABEL)
    written = write_pool(rows, pool, manifest, random.Random(7))
    assert len(written) == 2
    for path in written:
        body = path.read_text(encoding="utf-8")
        for marker in IDENTITY_MARKERS:
            assert marker not in body
        for row in rows:
            assert row.key not in body
    assert screen(pool) == []
    assert sorted(p.name for p in pool.glob("*.txt")) == ["001.txt", "002.txt"]


def test_manifest_holds_digests_and_no_content(tmp_path):
    pool, manifest = tmp_path / "pool", tmp_path / "manifest.txt"
    rows = parse_tally(fixture("tally-submissions.json"), LABEL)
    write_pool(rows, pool, manifest, random.Random(7))
    body = manifest.read_text(encoding="utf-8")
    assert "sub_aaa" not in body and "sub_bbb" not in body
    assert "SURVEY CONTRIBUTION" not in body
    lines = [line for line in body.splitlines() if line.strip()]
    assert len(lines) == 2
    assert all(line.startswith("sha256:") for line in lines)


def test_manifest_cannot_be_joined_to_the_pool(tmp_path):
    # The manifest and the pool must not be joinable by anyone reading the
    # checkout: no manifest line may contain any input key, across more than
    # one increment, and the manifest alone must give no way to tell which
    # pool file holds which text.
    pool, manifest = tmp_path / "pool", tmp_path / "manifest.txt"
    first = parse_tally(fixture("tally-submissions.json"), LABEL)
    write_pool(first, pool, manifest, random.Random(7))
    second = [
        Row("sub_ccc", "SURVEY CONTRIBUTION\n- a later submission, its own key"),
        Row("sub_ddd", "SURVEY CONTRIBUTION\n- and another one"),
    ]
    write_pool(second, pool, manifest, random.Random(3))

    manifest_lines = [
        line for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    all_keys = [row.key for row in [*first, *second]]
    for line in manifest_lines:
        assert line.startswith("sha256:")
        for key in all_keys:
            assert key not in line

    pool_bodies = [p.read_text(encoding="utf-8") for p in pool.glob("*.txt")]
    for body in pool_bodies:
        for line in manifest_lines:
            assert line not in body


def test_a_second_run_adds_only_what_is_new(tmp_path):
    pool, manifest = tmp_path / "pool", tmp_path / "manifest.txt"
    rows = parse_tally(fixture("tally-submissions.json"), LABEL)
    write_pool(rows, pool, manifest, random.Random(7))
    again = write_pool(rows, pool, manifest, random.Random(7))
    assert again == []
    assert len(list(pool.glob("*.txt"))) == 2


def test_new_files_are_numbered_past_the_highest_existing(tmp_path):
    pool, manifest = tmp_path / "pool", tmp_path / "manifest.txt"
    pool.mkdir()
    (pool / "007.txt").write_text("SURVEY CONTRIBUTION\n- typed from paper\n", encoding="utf-8")
    written = write_pool([Row("sub_new", "SURVEY CONTRIBUTION\n- a new one")], pool, manifest, random.Random(1))
    assert [p.name for p in written] == ["008.txt"]
    assert (pool / "007.txt").read_text(encoding="utf-8").endswith("paper\n")


def test_write_pool_raises_when_a_collision_is_forced_via_monkeypatch(tmp_path, monkeypatch):
    # The FileExistsError guard cannot fire through ordinary numbering: start
    # is always one past the highest existing numeric stem, so the freshly
    # computed target is never already on disk (proven by mutation — deleting
    # the raise leaves this suite green). A concurrent export, or an operator
    # hand-typing paper-fallback files mid-run, could still collide for real,
    # so the guard stays. This test forces that collision directly instead of
    # relying on numbering to produce one, which it structurally cannot.
    pool, manifest = tmp_path / "pool", tmp_path / "manifest.txt"
    pool.mkdir()
    target = pool / "001.txt"  # numbering starts at 1 for an empty pool

    real_exists = Path.exists

    def faked_exists(self, *args, **kwargs):
        # Only lie about the exact target write_pool is about to write.
        # Everything else (the manifest check, etc.) gets the real answer.
        if self == target:
            return True
        return real_exists(self, *args, **kwargs)

    monkeypatch.setattr(Path, "exists", faked_exists)

    with pytest.raises(FileExistsError):
        write_pool([Row("k", "text")], pool, manifest, random.Random(1))


def test_sorted_manifest_defeats_the_positional_join(tmp_path):
    # Digesting the key (tested above) blocks a passive read of the
    # checkout. It does not block the adversary who actually matters: one
    # with live provider API access, which is what turns a submission id
    # into a respondentId and a timestamp anyway. That same access lets
    # them enumerate candidate submission ids and hash every one — so the
    # digest itself is not a wall for them. If the manifest still kept
    # write_pool's append order, position alone would then complete the
    # join: manifest line i names pool file i, every time, by construction.
    # This test proves that join is dead once the manifest is sorted.
    pool, manifest = tmp_path / "pool", tmp_path / "manifest.txt"
    first = [Row(f"key-a{i}", f"SURVEY CONTRIBUTION\n- statement a{i}") for i in range(6)]
    second = [Row(f"key-b{i}", f"SURVEY CONTRIBUTION\n- statement b{i}") for i in range(6)]
    write_pool(first, pool, manifest, random.Random(1))
    write_pool(second, pool, manifest, random.Random(1))
    all_rows = first + second

    # What write_pool actually stores on disk: rstripped, newline-terminated.
    key_by_stored_text = {row.text.rstrip() + "\n": row.key for row in all_rows}

    def digest_of(key: str) -> str:
        # Reimplemented independently of tools.ingest._digest — this is the
        # attacker's move, not the module's: hash every candidate key you
        # can enumerate from the provider API and see what matches.
        return "sha256:" + hashlib.sha256(key.encode("utf-8")).hexdigest()

    manifest_lines = [
        line for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    pool_files = sorted(pool.glob("*.txt"))
    assert len(manifest_lines) == len(pool_files) == len(all_rows)

    # The manifest is still complete enough to deduplicate: every line is
    # the digest of some real input key, and every input key is digested
    # somewhere in there.
    expected_digests = {digest_of(row.key) for row in all_rows}
    assert set(manifest_lines) == expected_digests

    # Brute-force reversal over the candidate set succeeds for every single
    # line — that was never in doubt; hashing doesn't resist an adversary
    # who already holds the candidate keys. What must NOT also succeed is
    # pairing manifest line i with the i-th pool file to recover which
    # submission landed in which file. Under append order this recovers all
    # of them; under sorted order, position carries no information, so it
    # should recover at most one — no better than chance.
    hits = 0
    for line, path in zip(manifest_lines, pool_files):
        recovered_key = next(row.key for row in all_rows if digest_of(row.key) == line)
        actual_key = key_by_stored_text[path.read_text(encoding="utf-8")]
        if recovered_key == actual_key:
            hits += 1

    assert hits <= 1, (
        f"positional join recovered {hits}/{len(pool_files)} pairings — "
        "the manifest is not being written in sorted order"
    )


def test_order_is_shuffled_within_an_increment(tmp_path):
    rows = [Row(f"k{i}", f"SURVEY CONTRIBUTION\n- statement {i}") for i in range(12)]
    orders = set()
    for seed in (1, 2, 3, 4, 5):
        pool = tmp_path / f"pool{seed}"
        write_pool(rows, pool, tmp_path / f"m{seed}.txt", random.Random(seed))
        first = (pool / "001.txt").read_text(encoding="utf-8")
        orders.add(first)
    assert len(orders) > 1, "the pool is not being shuffled"
