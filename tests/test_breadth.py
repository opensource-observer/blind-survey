from dataclasses import replace
from pathlib import Path

import pytest

from tools.breadth import describe, tally
from tools.config import QUANTIFIERS, load_survey

SURVEY = load_survey(Path("survey.yaml"))


def with_min(size: int):
    return replace(SURVEY, anonymity=replace(SURVEY.anonymity, min_cell_size=size))


def test_a_cell_below_the_minimum_returns_a_quantifier():
    assert describe(4, 40, with_min(5)) in QUANTIFIERS


def test_a_cell_at_the_minimum_returns_a_number():
    assert describe(5, 40, with_min(5)) == 5


def test_a_cell_whose_complement_is_too_small_is_suppressed():
    # 5 of 6 clears the minimum itself but names the one person who differed.
    assert describe(5, 6, with_min(5)) in QUANTIFIERS


def test_a_cell_holding_everyone_returns_a_number():
    # Unanimity singles nobody out.
    assert describe(6, 6, with_min(5)) == 6


def test_a_single_holder_reads_as_isolated():
    assert describe(1, 40, with_min(5)) == "an isolated view"


def test_a_large_share_reads_as_broad_consensus():
    assert describe(30, 40, with_min(50)) == "broad consensus"


def test_a_middling_share_reads_as_several():
    assert describe(16, 40, with_min(50)) == "several respondents"


def test_a_small_share_reads_as_a_minority():
    assert describe(8, 40, with_min(50)) == "a minority view"


def test_the_judgment_call_quantifiers_are_never_returned():
    reserved = {
        "an isolated but strategically important view",
        "contested — no side holds more of the room",
    }
    produced = {describe(n, 40, with_min(50)) for n in range(1, 41)}
    assert not produced & reserved


def test_describing_nothing_is_an_error():
    with pytest.raises(ValueError, match="nothing to describe"):
        describe(0, 40, SURVEY)


def test_count_above_total_is_an_error():
    with pytest.raises(ValueError, match="more than the total"):
        describe(9, 8, SURVEY)


def test_tally_groups_by_facet_and_describes_each_cell():
    records = (
        [{"role": "maintainer"}] * 6
        + [{"role": "funder"}] * 2
        + [{"role": "user"}] * 1
    )
    out = tally(records, "role", with_min(3))
    assert out["maintainer"] == 6
    assert out["funder"] in QUANTIFIERS
    assert out["user"] == "an isolated view"


def test_tally_rejects_a_facet_that_is_not_declared():
    with pytest.raises(ValueError, match="not a declared facet"):
        tally([{"role": "funder"}], "sentiment", SURVEY)


def test_tally_skips_records_missing_the_facet():
    out = tally([{"role": "funder"}, {"statement": "x"}], "role", with_min(1))
    assert out == {"funder": 1}
