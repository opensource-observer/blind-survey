from pathlib import Path

from tools.check_pool import main, screen


def pool_with(tmp_path: Path, **files: str) -> Path:
    pool = tmp_path / "pool"
    pool.mkdir()
    for name, body in files.items():
        (pool / f"{name}.txt").write_text(body, encoding="utf-8")
    return pool


CLEAN = "SURVEY CONTRIBUTION\n- I believe the review burden grows faster than the contributor base\n"


def test_a_clean_pool_has_no_hits(tmp_path):
    assert screen(pool_with(tmp_path, **{"001": CLEAN})) == []


def test_a_leaked_provider_column_is_a_hit(tmp_path):
    pool = pool_with(tmp_path, **{"001": "Respondent ID: resp_111\n" + CLEAN})
    hits = screen(pool)
    assert len(hits) == 1
    assert hits[0].pattern == "provider field"


def test_an_iso_date_is_a_hit(tmp_path):
    hits = screen(pool_with(tmp_path, **{"001": CLEAN + "- submitted 2026-08-09\n"}))
    assert [h.pattern for h in hits] == ["date"]


def test_an_email_is_a_hit(tmp_path):
    hits = screen(pool_with(tmp_path, **{"001": CLEAN + "- mail security@example.org\n"}))
    assert [h.pattern for h in hits] == ["email"]


def test_a_url_is_a_hit(tmp_path):
    hits = screen(pool_with(tmp_path, **{"001": CLEAN + "- see https://example.org/x\n"}))
    assert [h.pattern for h in hits] == ["link"]


def test_a_hit_carries_the_offending_line(tmp_path):
    hits = screen(pool_with(tmp_path, **{"001": CLEAN + "- submitted 2026-08-09\n"}))
    assert "2026-08-09" in hits[0].line


def test_a_missing_pool_is_not_a_crash(tmp_path):
    assert screen(tmp_path / "absent") == []


def test_main_is_advisory_by_default(tmp_path, capsys):
    pool = pool_with(tmp_path, **{"001": CLEAN + "- see https://example.org/x\n"})
    assert main(["--pool", str(pool)]) == 0
    assert "link" in capsys.readouterr().out


def test_strict_mode_fails_on_a_hit(tmp_path):
    pool = pool_with(tmp_path, **{"001": CLEAN + "- see https://example.org/x\n"})
    assert main(["--pool", str(pool), "--strict"]) == 1


def test_strict_mode_passes_a_clean_pool(tmp_path):
    assert main(["--pool", str(pool_with(tmp_path, **{"001": CLEAN})), "--strict"]) == 0


def test_main_reports_a_missing_pool_and_fails(tmp_path, capsys):
    """A missing pool must not read as `clean` — a typo'd path (the day
    `examples/oso-ecosystem/pool` gets renamed, say) would otherwise pass
    CI's screening step silently, every time, forever."""
    missing = tmp_path / "does" / "not" / "exist"
    assert main(["--pool", str(missing)]) != 0
    assert "no such directory" in capsys.readouterr().out


def test_main_fails_on_a_missing_pool_even_without_strict(tmp_path):
    """A typo'd path is an operator error either way, not just under CI's
    --strict flag."""
    missing = tmp_path / "does" / "not" / "exist"
    assert main(["--pool", str(missing)]) != 0


def test_main_fails_on_a_missing_pool_with_strict(tmp_path):
    missing = tmp_path / "does" / "not" / "exist"
    assert main(["--pool", str(missing), "--strict"]) != 0
