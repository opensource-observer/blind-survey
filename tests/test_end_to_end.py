from pathlib import Path

from build.compile import SOURCES, compile_source
from tools.breadth import tally
from tools.check_pool import screen
from tools.config import QUANTIFIERS, load_survey
from tools.validate import check_all, load_jsonl

EXAMPLE = Path("examples/oso-ecosystem")
SURVEY = load_survey(Path("survey.yaml"))


def test_the_example_pool_is_clean():
    assert screen(EXAMPLE / "pool") == []


def test_the_example_pool_carries_the_configured_block_header():
    files = sorted((EXAMPLE / "pool").glob("*.txt"))
    assert len(files) >= 6
    for path in files:
        assert path.read_text(encoding="utf-8").startswith(
            SURVEY.submission.block_header
        )


def test_the_worked_statements_validate():
    records = load_jsonl(EXAMPLE / "statements.jsonl")
    assert records
    assert check_all(records, SURVEY) == []


def test_every_pool_bullet_produced_exactly_one_statement():
    bullets = sum(
        line.startswith("- ")
        for path in (EXAMPLE / "pool").glob("*.txt")
        for line in path.read_text(encoding="utf-8").splitlines()
    )
    assert len(load_jsonl(EXAMPLE / "statements.jsonl")) == bullets


def test_the_worked_statements_hold_an_unresolved_referent():
    records = load_jsonl(EXAMPLE / "statements.jsonl")
    assert any(r["role"] == "unspecified" for r in records)


def test_breadth_over_the_worked_statements_never_leaks_a_small_cell():
    records = load_jsonl(EXAMPLE / "statements.jsonl")
    for facet in SURVEY.facet_names:
        for value, breadth in tally(records, facet, SURVEY).items():
            assert isinstance(breadth, int) or breadth in QUANTIFIERS


def test_both_participant_artifacts_compile():
    for name, src in SOURCES.items():
        out = compile_source(src, SURVEY)
        assert out.strip()
        assert "<!--" not in out and "{{" not in out


def test_the_analyze_steps_exist_and_name_their_inputs():
    atomize = Path("skills/operator/analyze/steps/01-atomize.md").read_text(encoding="utf-8")
    cluster = Path("skills/operator/analyze/steps/02-cluster.md").read_text(encoding="utf-8")
    assert "private/pool" in atomize
    assert "private/pool" not in cluster, "step 2 must never read the pool"
    assert "breadth.py" in cluster
