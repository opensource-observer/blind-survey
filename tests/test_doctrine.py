from pathlib import Path

import pytest

from tools.config import CONFIDENCE_TIERS, QUANTIFIERS

HEADINGS = {
    "rules/anonymity.md": "## Rules: anonymity and disclosure",
    "rules/statement-style.md": "## Rules: statement style",
    "rules/quantifiers.md": "## Rules: reporting breadth",
}


@pytest.mark.parametrize("path,heading", sorted(HEADINGS.items()))
def test_rule_file_exists_with_its_exact_heading(path, heading):
    text = Path(path).read_text(encoding="utf-8")
    assert text.startswith(heading + "\n"), f"{path} must open with {heading!r}"


def test_quantifier_rule_lists_all_five_verbatim():
    text = Path("rules/quantifiers.md").read_text(encoding="utf-8")
    for quantifier in QUANTIFIERS:
        assert quantifier in text, f"missing quantifier: {quantifier!r}"


def test_statement_style_names_each_confidence_preamble():
    text = Path("rules/statement-style.md").read_text(encoding="utf-8")
    for preamble in ("I'm confident that", "I believe", "My hunch is"):
        assert preamble in text
    for tier in CONFIDENCE_TIERS:
        assert tier in text


def test_no_rule_file_uses_protocol_vocabulary():
    banned = ("atomize", "corroborate", "provenance", "constituency", "falsifiable")
    for path in HEADINGS:
        text = Path(path).read_text(encoding="utf-8").lower()
        for word in banned:
            assert word not in text, f"{path} uses {word!r}; rules are read by respondents"


def test_schema_documents_the_three_fixed_fields():
    text = Path("rules/statement-schema.md").read_text(encoding="utf-8")
    for field in ("statement", "confidence", "submission"):
        assert field in text
    assert "survey.yaml" in text
