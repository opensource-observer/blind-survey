"""Every entry point here is documented as `uv run python <path>.py` — a bare
script invocation, not `python -m tools.validate`. Every one of these modules
imports `tools.config` with an absolute import, which only resolves if the
repo root is on `sys.path`. Each module carries a `sys.path.insert(0, ...)`
shim near its top for exactly that reason: pytest never needs it, because
`pyproject.toml` sets `pythonpath = ["."]`, but a bare script invocation gets
no such help and dies with `ModuleNotFoundError` without the shim.

That exact regression shipped four separate times during this build, and
every time it slipped through because the existing tests called functions
directly and never spawned the process the documented command actually
spawns. This test spawns it.

`tools/breadth.py` is run with real arguments rather than `--help`: its
`main()` imports `tools.validate.load_jsonl` lazily, after argparse has
already succeeded, and `--help` makes argparse exit before that import is
ever reached — which would leave the import itself untested.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from tools.config import ROOT

# (script, args). `build/compile.py` takes no arguments and does real work
# (it recompiles dist/ from the current survey.yaml) — it has no --help, so
# it is run bare. The five modules under tools/ are argparse CLIs, so --help
# is the side-effect-free way to spawn each one and still exercise the import.
ENTRYPOINTS = (
    ("build/compile.py", ()),
    ("tools/validate.py", ("--help",)),
    ("tools/breadth.py", ("examples/oso-ecosystem/statements.jsonl", "role")),
    ("tools/check_pool.py", ("--help",)),
    ("tools/verify_form.py", ("--help",)),
    ("tools/ingest.py", ("--help",)),
)


@pytest.mark.parametrize(
    "script,args", ENTRYPOINTS, ids=[script for script, _ in ENTRYPOINTS]
)
def test_entrypoint_runs_as_a_bare_script(script, args):
    result = subprocess.run(
        [sys.executable, script, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert "ModuleNotFoundError" not in result.stderr, (
        f"{script} died on import when run as a bare script — "
        f"the sys.path shim is missing or broken. stderr:\n{result.stderr}"
    )
    assert result.returncode == 0, (
        f"{script} exited {result.returncode}. stderr:\n{result.stderr}"
    )
