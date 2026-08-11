import json
from dataclasses import replace
from pathlib import Path

from tools.config import load_survey
from tools.validate import check_all, check_record, load_jsonl

SURVEY = load_survey(Path("survey.yaml"))

OK = {
    "statement": "The review burden grows faster than the contributor base",
    "confidence": "medium",
    "kind": "belief",
    "subject_role": "maintainer",
    "scope": "community",
}


def check(**overrides):
    record = {**OK, **overrides}
    for key, value in list(record.items()):
        if value is ...:
            del record[key]
    return check_record(record, 1, SURVEY)


def messages(findings):
    return " | ".join(f.message for f in findings)


def test_the_good_fixture_is_clean():
    records = load_jsonl(Path("tests/fixtures/statements-good.jsonl"))
    assert len(records) == 4
    assert check_all(records, SURVEY) == []


def test_missing_statement_is_a_finding():
    assert "statement" in messages(check(statement=...))


def test_empty_statement_is_a_finding():
    assert "empty" in messages(check(statement="   "))


def test_unknown_confidence_is_a_finding():
    assert "confidence" in messages(check(confidence="quite sure"))


def test_numeric_confidence_says_so_explicitly():
    assert "numeric" in messages(check(confidence=0.8))


def test_missing_facet_is_a_finding():
    assert "kind" in messages(check(kind=...))


def test_facet_value_outside_its_list_is_a_finding():
    assert "vibe" in messages(check(kind="vibe"))


def test_undeclared_key_is_a_finding():
    assert "respondent_id" in messages(check(respondent_id="r_12"))


def test_submission_is_an_undeclared_key():
    assert "undeclared key 'submission'" in messages(check(submission="a1b2"))


def test_explicit_null_submission_is_still_an_undeclared_key():
    assert "undeclared key 'submission'" in messages(check(submission=None))


def test_iso_date_in_statement_text_is_a_finding():
    assert "date" in messages(check(statement="Adoption stalled after 2026-03-14"))


def test_bare_year_in_statement_text_is_a_finding():
    assert "year" in messages(check(statement="The rewrite slipped past 2025 entirely"))


def test_relative_time_in_statement_text_is_a_finding():
    assert "time" in messages(check(statement="Maintainer numbers fell last quarter"))


def test_email_in_statement_text_is_a_finding():
    assert "email" in messages(check(statement="Reports go to security@example.org and stall"))


def test_url_in_statement_text_is_a_finding():
    assert "link" in messages(check(statement="The policy lives at https://example.org/policy"))


def test_handle_in_statement_text_is_a_finding():
    assert "handle" in messages(check(statement="Most triage falls to @onemaintainer"))


def test_email_in_a_hand_added_submission_field_is_still_screened():
    findings = check_record({**OK, "submission": "someone@example.org"}, 1, SURVEY)
    assert "email" in messages(findings)
    assert [f.field for f in findings if "email" in f.message] == ["submission"]


def test_url_in_a_hand_added_submission_field_is_still_screened():
    findings = check_record({**OK, "submission": "https://tally.so/r/2EzdJA"}, 1, SURVEY)
    assert "link" in messages(findings)
    assert [f.field for f in findings if "link" in f.message] == ["submission"]


def test_stoplist_word_is_a_finding():
    stopped = replace(SURVEY, stoplist=("Meridian",))
    findings = check_record(
        {**OK, "statement": "Meridian pays for most of the tooling"}, 1, stopped
    )
    assert "stoplist" in messages(findings)


def test_findings_carry_their_line_number():
    records = [OK, {**OK, "confidence": "certain"}]
    findings = check_all(records, SURVEY)
    assert [f.line for f in findings] == [2]
