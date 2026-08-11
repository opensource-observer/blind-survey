import subprocess
import sys
from pathlib import Path

import pytest

from build.compile import CompileError, compile_source
from tools.config import ROOT, load_survey

SURVEY = load_survey(Path("survey.yaml"))


def src(tmp_path: Path, body: str, name: str = "SKILL.md") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_include_is_inlined(tmp_path):
    (tmp_path / "rules").mkdir()
    (tmp_path / "rules" / "r.md").write_text("## Rules: a rule\n\nBody.\n", encoding="utf-8")
    out = compile_source(src(tmp_path, "Top\n\n<!-- include:rules/r.md -->\n"), SURVEY, tmp_path)
    assert "## Rules: a rule" in out
    assert "Body." in out
    assert "include:" not in out


def test_missing_include_fails_the_build(tmp_path):
    with pytest.raises(CompileError, match="missing include"):
        compile_source(src(tmp_path, "<!-- include:rules/gone.md -->\n"), SURVEY, tmp_path)


def test_nested_or_malformed_include_marker_fails(tmp_path):
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, "<!-- include: bad path.md -->\n"), SURVEY, tmp_path)


def test_scalar_field_is_substituted(tmp_path):
    out = compile_source(src(tmp_path, "Takes {{ survey.duration_minutes }} minutes.\n"), SURVEY, tmp_path)
    assert "Takes 15 minutes." in out


def test_nested_field_is_substituted(tmp_path):
    out = compile_source(src(tmp_path, "Header: {{ survey.submission.block_header }}\n"), SURVEY, tmp_path)
    assert "Header: SURVEY CONTRIBUTION" in out


def test_questions_render_as_a_numbered_list(tmp_path):
    out = compile_source(src(tmp_path, "{{ survey.questions }}\n"), SURVEY, tmp_path)
    assert out.startswith("1. What is the biggest risk")
    assert f"{len(SURVEY.questions)}. " in out


def test_unknown_field_fails_the_build(tmp_path):
    with pytest.raises(CompileError, match="no field"):
        compile_source(src(tmp_path, "{{ survey.nonesuch }}\n"), SURVEY, tmp_path)


def test_stray_template_marker_fails_the_build(tmp_path):
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, "{{ notsurvey.thing }}\n"), SURVEY, tmp_path)


def test_tight_conditional_marker_fails_the_build(tmp_path):
    body = "A\n<!-- if:survey.title -->\nGUARDED\n<!-- endif -->\nB\n"
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, body), SURVEY, tmp_path)


def test_spaced_conditional_marker_fails_the_build(tmp_path):
    """The bug this guards: a marker with a typo'd space matched neither the
    conditional pattern nor the safety net, so it was stripped as an ordinary
    comment and the guarded body shipped into a document a respondent reads."""
    body = "A\n<!-- if : survey.title -->\nGUARDED\n<!-- endif -->\nB\n"
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, body), SURVEY, tmp_path)


def test_conditional_on_a_falsy_field_fails_instead_of_dropping_its_body(tmp_path):
    # survey.submission.form_id is null. The compiler used to drop the body
    # silently; failing the build is the only safe answer now.
    body = "<!-- if:survey.submission.form_id -->\nGUARDED\n<!-- endif -->\n"
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, body), SURVEY, tmp_path)


def test_stray_endif_fails_the_build(tmp_path):
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, "A\n<!-- endif -->\nB\n"), SURVEY, tmp_path)


def test_maintainer_comments_are_stripped(tmp_path):
    out = compile_source(src(tmp_path, "Visible.\n<!-- a note to maintainers -->\nAlso visible.\n"), SURVEY, tmp_path)
    assert "note to maintainers" not in out
    assert "Visible." in out and "Also visible." in out


def test_absolute_include_path_escapes_the_root(tmp_path):
    with pytest.raises(CompileError, match="escapes the root"):
        compile_source(src(tmp_path, "<!-- include:/etc/passwd -->\n"), SURVEY, tmp_path)


def test_traversal_include_path_escapes_the_root(tmp_path):
    with pytest.raises(CompileError, match="escapes the root"):
        compile_source(
            src(tmp_path, "<!-- include:../../../../../../etc/hostname -->\n"), SURVEY, tmp_path
        )


def test_legitimate_include_still_resolves_after_containment_check(tmp_path):
    (tmp_path / "rules").mkdir()
    (tmp_path / "rules" / "r.md").write_text("## Rules: a rule\n\nBody.\n", encoding="utf-8")
    out = compile_source(src(tmp_path, "Top\n\n<!-- include:rules/r.md -->\n"), SURVEY, tmp_path)
    assert "## Rules: a rule" in out
    assert "Body." in out
    assert "include:" not in out


def test_maintainer_note_starting_with_if_compiles_cleanly(tmp_path):
    out = compile_source(
        src(tmp_path, "A\n<!-- if this doesn't work, ask the maintainer -->\nB\n"), SURVEY, tmp_path
    )
    assert "if this doesn't work" not in out
    assert "A" in out and "B" in out


def test_maintainer_note_starting_with_include_compiles_cleanly(tmp_path):
    out = compile_source(
        src(tmp_path, "A\n<!-- include a citation later -->\nB\n"), SURVEY, tmp_path
    )
    assert "include a citation later" not in out
    assert "A" in out and "B" in out


def test_uppercase_conditional_marker_fails_the_build(tmp_path):
    """The bug this guards: UNRESOLVED_RE only matched lowercase, so
    `<!-- IF:… -->` / `<!-- ENDIF -->` parsed as an ordinary HTML comment and
    the guarded body shipped into a document a respondent reads."""
    body = "A\n<!-- IF:survey.title -->\nGUARDED\n<!-- ENDIF -->\nB\n"
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, body), SURVEY, tmp_path)


def test_mixed_case_conditional_marker_fails_the_build(tmp_path):
    body = "A\n<!-- If:survey.title -->\nGUARDED\n<!-- EndIf -->\nB\n"
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, body), SURVEY, tmp_path)


def test_uppercase_include_marker_fails_the_build(tmp_path):
    """Deliberate consequence of the case-insensitive guard: an uppercase
    INCLUDE marker now fails loudly instead of silently failing to resolve
    and being stripped as an ordinary comment."""
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, "<!-- INCLUDE:rules/anonymity.md -->\n"), SURVEY, tmp_path)


def test_case_variant_conditional_markers_never_leak_the_guarded_body(tmp_path):
    """Belt-and-suspenders on top of the two `fails_the_build` tests above:
    even if the case-insensitive guard ever regressed and stopped raising,
    the guarded body must still never reach anything that looks like
    compiled output — that leak is the entire bug being fixed here."""
    for name, body in (
        ("upper", "<!-- IF:survey.title -->\nGUARDED\n<!-- ENDIF -->\n"),
        ("mixed", "<!-- If:survey.title -->\nGUARDED\n<!-- EndIf -->\n"),
    ):
        path = src(tmp_path, body, name=f"{name}.md")
        raised = False
        try:
            out = compile_source(path, SURVEY, tmp_path)
        except CompileError:
            raised = True
        assert raised, f"{name} case did not raise CompileError"
        if not raised:
            assert "GUARDED" not in out


def test_dunder_field_fails_the_build(tmp_path):
    with pytest.raises(CompileError, match="no field"):
        compile_source(src(tmp_path, "{{ survey.__init__ }}\n"), SURVEY, tmp_path)


def test_property_field_is_substituted(tmp_path):
    out = compile_source(src(tmp_path, "{{ survey.facet_names }}\n"), SURVEY, tmp_path)
    assert "kind" in out
    assert "role" in out
    assert "scope" in out


def test_orphaned_if_marker_with_whitespace_around_colon_fails_the_build(tmp_path):
    with pytest.raises(CompileError, match="unresolved"):
        compile_source(src(tmp_path, "<!-- if : survey.name -->\n"), SURVEY, tmp_path)


def test_include_marker_with_whitespace_around_colon_resolves(tmp_path):
    (tmp_path / "rules").mkdir()
    (tmp_path / "rules" / "r.md").write_text("## Rules: a rule\n\nBody.\n", encoding="utf-8")
    out = compile_source(src(tmp_path, "<!-- include : rules/r.md -->\n"), SURVEY, tmp_path)
    assert "## Rules: a rule" in out
    assert "Body." in out


def test_callable_field_fails_the_build(tmp_path):
    with pytest.raises(CompileError, match="no field"):
        compile_source(src(tmp_path, "{{ survey.questions.count }}\n"), SURVEY, tmp_path)


def test_script_entrypoint_works_as_a_bare_script_invocation():
    """`uv run python build/compile.py` is the documented command, run by an
    audience that cannot be asked to know about `-m`. Importing main() would
    not catch a sys.path regression here — this has to actually spawn the
    interpreter the way a person does."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "build" / "compile.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    for name in ("interview", "trust-brief"):
        target = ROOT / "dist" / f"{name}.md"
        assert target.exists(), result.stderr
        assert target.read_text(encoding="utf-8").strip(), result.stderr
