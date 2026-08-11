"""Compile participant sources into self-contained artifacts under dist/.

Two markers, resolved in this order:

  <!-- include:<repo-relative-path> -->   inline a file
  {{ survey.<dotted.path> }}              substitute a config value

Conditionals are not supported. A source carrying `<!-- if:… -->` or
`<!-- endif -->` fails the build, in any spelling, rather than compiling to a
document that quietly keeps or drops the guarded body. Any marker of any kind
left over fails the build for the same reason: a compiled artifact is read by a
respondent, and it must not ship with a hole in it. Remaining HTML comments are
maintainer notes, and are stripped only after that check passes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# `uv run python build/compile.py` — the documented command, since the
# audience for this repo cannot be asked to know about `-m` — only puts this
# file's own directory on sys.path, not the repo root. The absolute
# `tools.config` import below would fail without this. pytest gets away
# without it because pyproject.toml sets pythonpath = ["."].
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.config import ROOT, Survey, load_survey  # noqa: E402

SOURCES = {
    "interview": ROOT / "skills" / "participant" / "interview" / "SKILL.md",
    "trust-brief": ROOT / "templates" / "trust-brief.md",
}

INCLUDE_RE = re.compile(r"<!--\s*include\s*:\s*(?P<path>[\w\-/.]+)\s*-->[ \t]*\n?")
FIELD_RE = re.compile(r"\{\{\s*survey\.(?P<path>[\w.]+)\s*\}\}")
# Catches `if` and `endif` too, even though nothing resolves them: a conditional
# has to fail the build loudly, never get stripped as an ordinary comment and
# ship its guarded body into a document a respondent reads. Case-insensitive on
# purpose: `<!-- IF:… -->` or `<!-- If:… -->` is just as much a conditional as
# the lowercase spelling, and letting capitalization dodge this check is the
# same failure all over again. INCLUDE_RE and FIELD_RE below stay
# case-sensitive — markers are lowercase by convention, and only this guard's
# job is to catch anything that merely looks like an attempt.
UNRESOLVED_RE = re.compile(
    r"<!--\s*(?:if\s*:|include\s*:)|<!--\s*endif\s*-->|\{\{",
    re.IGNORECASE,
)
COMMENT_LINE_RE = re.compile(r"^[ \t]*<!--.*?-->[ \t]*\n", re.DOTALL | re.MULTILINE)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


class CompileError(ValueError):
    """A source could not be compiled into a shippable artifact."""


def _lookup(survey: Survey, dotted: str) -> object:
    node: object = survey
    for part in dotted.split("."):
        if part.startswith("_") or not hasattr(node, part):
            raise CompileError(f"survey has no field {dotted!r}")
        node = getattr(node, part)
    if callable(node):
        raise CompileError(f"survey has no field {dotted!r}")
    return node


def _format(value: object) -> str:
    if isinstance(value, tuple):
        return "\n".join(f"{i}. {item}" for i, item in enumerate(value, 1))
    if value is None:
        return ""
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return str(value)


def compile_source(src: Path, survey: Survey, root: Path = ROOT) -> str:
    text = src.read_text(encoding="utf-8")
    resolved_root = root.resolve()

    def inline(match: re.Match[str]) -> str:
        raw_path = match.group("path")
        target = (root / raw_path).resolve()
        if not target.is_relative_to(resolved_root):
            raise CompileError(f"{src}: include {raw_path!r} escapes the root")
        if not target.exists():
            raise CompileError(f"{src}: missing include {raw_path!r}")
        return target.read_text(encoding="utf-8").rstrip() + "\n"

    def substitute(match: re.Match[str]) -> str:
        return _format(_lookup(survey, match.group("path")))

    text = INCLUDE_RE.sub(inline, text)
    text = FIELD_RE.sub(substitute, text)

    leftover = UNRESOLVED_RE.search(text)
    if leftover:
        line = text[: leftover.start()].count("\n") + 1
        raise CompileError(
            f"{src}: unresolved marker at line {line}: "
            f"{text[leftover.start(): leftover.start() + 40]!r}"
        )

    text = COMMENT_LINE_RE.sub("", text)
    return COMMENT_RE.sub("", text)


def main() -> int:
    survey = load_survey()
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for name, src in SOURCES.items():
        (dist / f"{name}.md").write_text(compile_source(src, survey), encoding="utf-8")
        print(f"compiled dist/{name}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
