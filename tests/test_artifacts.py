from pathlib import Path

import pytest

from tools.compile import SOURCES, compile_source
from tools.config import load_survey

SURVEY = load_survey(Path("survey.yaml"))
RULE_HEADINGS = (
    "## Rules: anonymity and disclosure",
    "## Rules: statement style",
)


@pytest.fixture(scope="module")
def interview() -> str:
    return compile_source(SOURCES["interview"], SURVEY)


@pytest.fixture(scope="module")
def brief() -> str:
    return compile_source(SOURCES["trust-brief"], SURVEY)


@pytest.mark.parametrize("heading", RULE_HEADINGS)
def test_interview_carries_every_rule_it_must(interview, heading):
    assert heading in interview


def test_interview_renders_every_question(interview):
    for question in SURVEY.questions:
        assert question in interview


def test_interview_states_the_duration(interview):
    assert str(SURVEY.duration_minutes) in interview


def test_interview_names_the_block_header(interview):
    assert SURVEY.submission.block_header in interview


def test_interview_states_the_expected_group_size(interview):
    """Two rules ask the interviewer to judge against the group size. The
    compiled prompt has to say what that size is."""
    assert f"{SURVEY.anonymity.expected_respondents} people" in interview


def test_interview_ships_no_markers_or_comments(interview):
    for marker in ("<!--", "{{", "include:", "endif"):
        assert marker not in interview


def test_interview_uses_no_protocol_vocabulary(interview):
    lowered = interview.lower()
    for word in ("atomize", "corroborate", "provenance", "constituency", "falsifiable", "as an ai"):
        assert word not in lowered


def test_interview_never_promises_automatic_submission(interview):
    assert "you" in interview.lower()
    assert "nothing is submitted automatically" in interview.lower()


def test_brief_carries_the_anonymity_rules(brief):
    assert "## Rules: anonymity and disclosure" in brief


def test_brief_states_the_expected_group_size(brief):
    assert f"{SURVEY.anonymity.expected_respondents} people" in brief


def test_brief_ships_no_markers(brief):
    for marker in ("<!--", "{{"):
        assert marker not in brief


def test_compiling_writes_both_artifacts(tmp_path, monkeypatch):
    import tools.compile as compile_mod

    monkeypatch.setattr(compile_mod, "ROOT", tmp_path)
    for name, src in SOURCES.items():
        target = tmp_path / "dist" / f"{name}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(compile_source(src, SURVEY), encoding="utf-8")
        assert target.read_text(encoding="utf-8").strip()
