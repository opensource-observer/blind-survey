import json
from dataclasses import replace
from pathlib import Path

import pytest

from tools.config import load_survey
from tools.verify_form import verify, verify_google, verify_tally

SURVEY = load_survey(Path("survey.yaml"))
GOOGLE_SURVEY = replace(
    SURVEY, submission=replace(SURVEY.submission, provider="google-forms")
)


def fixture(name: str) -> dict:
    return json.loads(Path(f"tests/fixtures/{name}").read_text(encoding="utf-8"))


def joined(report) -> str:
    return " | ".join(report.violations)


def test_compliant_tally_form_passes():
    report = verify_tally(fixture("tally-form-compliant.json"), SURVEY)
    assert report.ok
    assert report.violations == ()
    assert report.unverifiable == ()


@pytest.mark.parametrize(
    "needle",
    [
        "hasSelfEmailNotifications",
        "hasRespondentEmailNotifications",
        "hasPartialSubmissions",
        "uniqueSubmissionKey",
        "submissionsLimit",
        "password",
        "INPUT_EMAIL",
        "CAPTCHA",
        "required",
        "label",
        "PUBLISHED",
    ],
)
def test_each_tally_violation_is_reported(needle):
    report = verify_tally(fixture("tally-form-violations.json"), SURVEY)
    assert not report.ok
    assert needle in joined(report)


def test_a_form_with_a_dropdown_and_country_capture_is_rejected():
    report = verify_tally(fixture("tally-form-dropdown-country.json"), SURVEY)
    assert not report.ok
    assert "DROPDOWN_OPTION" in joined(report)
    assert "RESPONDENT_COUNTRY" in joined(report)


def test_a_closed_tally_form_is_rejected():
    form = fixture("tally-form-compliant.json")
    form["settings"]["isClosed"] = True
    report = verify_tally(form, SURVEY)
    assert not report.ok
    assert "closed" in joined(report)


def test_field_label_matches_when_rich_text_is_split_across_spans():
    form = fixture("tally-form-compliant.json")
    for block in form["blocks"]:
        if block["type"] == "TITLE":
            block["payload"]["safeHTMLSchema"] = [
                ["Paste your contribution ", "block here"]
            ]
    report = verify_tally(form, SURVEY)
    assert report.ok


def test_a_tally_form_with_two_input_blocks_is_rejected():
    form = fixture("tally-form-compliant.json")
    form["blocks"].append(
        {
            "uuid": "66666666-6666-4666-8666-666666666666",
            "type": "INPUT_TEXT",
            "groupUuid": "66666666-6666-4666-8666-666666666666",
            "groupType": "QUESTION",
            "payload": {"isRequired": False},
        }
    )
    assert "exactly one" in joined(verify_tally(form, SURVEY))


def test_compliant_google_form_passes_but_names_what_it_cannot_check():
    report = verify_google(fixture("google-form-compliant.json"), GOOGLE_SURVEY)
    assert report.ok
    assert len(report.unverifiable) == 3
    assert any("sign-in" in note for note in report.unverifiable)


def test_google_form_collecting_email_is_rejected():
    report = verify_google(fixture("google-form-verified-email.json"), GOOGLE_SURVEY)
    assert not report.ok
    assert "emailCollectionType" in joined(report)


def test_google_form_with_a_second_question_is_rejected():
    report = verify_google(fixture("google-form-verified-email.json"), GOOGLE_SURVEY)
    assert "exactly one" in joined(report)


def test_verify_dispatches_on_the_configured_provider():
    assert verify(fixture("tally-form-compliant.json"), SURVEY).ok
    assert verify(fixture("google-form-compliant.json"), GOOGLE_SURVEY).ok


def test_paper_provider_has_nothing_to_verify():
    paper = replace(SURVEY, submission=replace(SURVEY.submission, provider="paper"))
    report = verify({}, paper)
    assert report.ok
    assert any("paper" in note for note in report.unverifiable)
