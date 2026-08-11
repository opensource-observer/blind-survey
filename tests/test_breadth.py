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


def test_a_cell_at_the_minimum_returns_a_phrase_not_a_number():
    result = describe(5, 40, with_min(5))
    assert result == "limited evidence"
    assert isinstance(result, str)


def test_a_cell_near_unanimous_still_returns_a_phrase_not_a_number():
    # Five of six used to be suppressed for naming the one person who
    # differed. There is no number to suppress any more: this cell reads the
    # same as any other high-share cell, because nothing here ever counts
    # people in the first place.
    result = describe(5, 6, with_min(5))
    assert result == "a recurring theme"
    assert isinstance(result, str)


def test_a_cell_holding_everyone_still_returns_a_phrase():
    assert describe(6, 6, with_min(5)) == "a recurring theme"


def test_a_single_holder_reads_as_a_single_statement():
    assert describe(1, 40, with_min(5)) == "a single statement"


def test_a_large_share_reads_as_a_recurring_theme():
    assert describe(30, 40, with_min(5)) == "a recurring theme"


def test_a_middling_share_reads_as_appears_more_than_once():
    assert describe(16, 40, with_min(5)) == "appears more than once"


def test_a_small_share_reads_as_limited_evidence():
    assert describe(8, 40, with_min(5)) == "limited evidence"


def test_the_judgment_call_quantifier_is_never_returned():
    reserved = {"contested across the material"}
    produced = {describe(n, 40, with_min(5)) for n in range(1, 41)}
    assert not produced & reserved


def test_describing_nothing_is_an_error():
    with pytest.raises(ValueError, match="nothing to describe"):
        describe(0, 40, SURVEY)


def test_count_above_total_is_an_error():
    with pytest.raises(ValueError, match="more than the total"):
        describe(9, 8, SURVEY)


def test_tally_groups_by_facet_and_describes_each_cell():
    records = (
        [{"subject_role": "maintainer"}] * 6
        + [{"subject_role": "funder"}] * 2
        + [{"subject_role": "user"}] * 1
    )
    out = tally(records, "subject_role", with_min(3))
    assert out["maintainer"] == "a recurring theme"
    assert out["funder"] in QUANTIFIERS
    assert out["user"] == "a single statement"


def test_tally_rejects_a_facet_that_is_not_declared():
    with pytest.raises(ValueError, match="not a declared facet"):
        tally([{"subject_role": "funder"}], "sentiment", SURVEY)


def test_tally_skips_records_missing_the_facet():
    out = tally([{"subject_role": "funder"}, {"statement": "x"}], "subject_role", with_min(1))
    assert out == {"funder": "a single statement"}
