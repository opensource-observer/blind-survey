from pathlib import Path

import pytest

SKILLS = ("setup", "administer", "ingest", "analyze")


@pytest.mark.parametrize("name", SKILLS)
def test_each_operator_skill_exists(name):
    assert Path(f"skills/operator/{name}/SKILL.md").is_file()


@pytest.mark.parametrize("name", SKILLS)
def test_each_skill_is_reachable_from_dot_claude(name):
    link = Path(f".claude/skills/{name}")
    assert link.exists(), f"{link} is missing"
    assert link.resolve() == Path(f"skills/operator/{name}").resolve()


def test_setup_covers_every_stage_it_owns():
    text = Path("skills/operator/setup/SKILL.md").read_text(encoding="utf-8")
    for needed in (
        "survey.yaml",
        "build/compile.py",
        "verify_form.py",
        "api.tally.so/mcp",
        "DO_NOT_COLLECT",
        "throwaway",
    ):
        assert needed in text


def test_setup_asks_one_question_at_a_time():
    text = Path("skills/operator/setup/SKILL.md").read_text(encoding="utf-8").lower()
    assert "one question at a time" in text


def test_administer_reverifies_before_each_pull():
    text = Path("skills/operator/administer/SKILL.md").read_text(encoding="utf-8")
    assert "verify_form.py" in text
    assert "before" in text.lower()


def test_ingest_skill_forbids_pulling_submissions_through_mcp():
    text = Path("skills/operator/ingest/SKILL.md").read_text(encoding="utf-8")
    assert "tools/ingest.py" in text
    assert "MCP" in text
    assert "respondentId" in text
