"""Railway runs the app on the Docker image's Python (3.10, Ubuntu jammy). Newer syntax that compiles on the
developer's Python 3.12+ (e.g. backslashes or same quotes inside an f-string's {...}) breaks a whole kit there,
so every file must compile on 3.10."""
import pathlib, shutil, subprocess, sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CODE = ("import sys\nbad=[]\nfor f in sys.argv[1:]:\n    try: compile(open(f, encoding='utf-8').read(), f, 'exec')\n"
        "    except Exception as e: bad.append(f + ': ' + str(e)[:200])\nprint('\\n'.join(bad)); sys.exit(1 if bad else 0)")


def _py310():
    if shutil.which("python3.10"):
        return ["python3.10"]
    if shutil.which("uv"):
        return ["uv", "run", "--no-project", "--python", "3.10", "python"]
    return None


def test_every_file_compiles_on_python_310():
    cmd = _py310()
    if not cmd:
        pytest.skip("no Python 3.10 here (CI checks it)")
    files = [str(p) for p in ROOT.rglob("*.py") if ".venv" not in p.parts and "node_modules" not in p.parts]
    r = subprocess.run(cmd + ["-c", CODE] + files, capture_output=True, text=True, timeout=600)
    if r.returncode != 0 and "error" in r.stderr.lower() and not r.stdout.strip():
        pytest.skip("could not start Python 3.10: " + r.stderr[-200:])
    assert r.returncode == 0, r.stdout
