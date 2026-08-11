import textwrap
from pathlib import Path

import pytest

from tools.config import CONFIDENCE_TIERS, PROVIDERS, QUANTIFIERS, ConfigError, load_survey

MINIMAL = """
name: t
title: T
audience: a group
duration_minutes: 15
submission:
  provider: tally
  form_id: null
  form_url: null
  field_label: "Paste your contribution block here"
  block_header: SURVEY CONTRIBUTION
anonymity:
  expected_respondents: 50
  min_cell_size: 5
questions:
  - What broke?
facets:
  kind: [belief, unspecified]
stoplist: []
"""


def write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "survey.yaml"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def test_loads_the_shipped_example():
    survey = load_survey(Path("survey.yaml"))
    assert survey.name == "oso-ecosystem-sensing"
    assert survey.submission.provider == "tally"
    assert survey.anonymity.min_cell_size == 5
    assert len(survey.questions) >= 5
    assert "unspecified" in survey.facets["kind"]


def test_questions_and_facet_values_are_tuples(tmp_path):
    survey = load_survey(write(tmp_path, MINIMAL))
    assert isinstance(survey.questions, tuple)
    assert isinstance(survey.facets["kind"], tuple)


def test_missing_file_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="no survey config"):
        load_survey(tmp_path / "nope.yaml")


def test_missing_required_key_names_the_key(tmp_path):
    body = MINIMAL.replace("audience: a group\n", "")
    with pytest.raises(ConfigError, match="audience"):
        load_survey(write(tmp_path, body))


def test_unknown_provider_is_rejected(tmp_path):
    body = MINIMAL.replace("provider: tally", "provider: surveymonkey")
    with pytest.raises(ConfigError, match="provider"):
        load_survey(write(tmp_path, body))


def test_min_cell_size_below_one_is_rejected(tmp_path):
    body = MINIMAL.replace("min_cell_size: 5", "min_cell_size: 0")
    with pytest.raises(ConfigError, match="min_cell_size"):
        load_survey(write(tmp_path, body))


def test_empty_questions_is_rejected(tmp_path):
    body = MINIMAL.replace("  - What broke?\n", "")
    with pytest.raises(ConfigError, match="questions"):
        load_survey(write(tmp_path, body))


def test_facet_without_unspecified_is_rejected(tmp_path):
    body = MINIMAL.replace("kind: [belief, unspecified]", "kind: [belief, risk]")
    with pytest.raises(ConfigError, match="unspecified"):
        load_survey(write(tmp_path, body))


def test_expected_respondents_below_one_is_rejected(tmp_path):
    body = MINIMAL.replace("expected_respondents: 50", "expected_respondents: 0")
    with pytest.raises(ConfigError, match="expected_respondents"):
        load_survey(write(tmp_path, body))


def test_statement_keys_hold_no_submission_field(tmp_path):
    survey = load_survey(write(tmp_path, MINIMAL))
    assert "submission" not in survey.statement_keys
    assert survey.statement_keys == ("statement", "confidence", "kind")


def test_constants_are_fixed():
    assert PROVIDERS == ("tally", "google-forms", "paper")
    assert CONFIDENCE_TIERS == ("high", "medium", "low")
    assert len(QUANTIFIERS) == 6
    assert QUANTIFIERS[0] == "broad consensus"
    assert QUANTIFIERS[-1] == "contested — no side holds more of the room"
