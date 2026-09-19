"""Packaging claims that the code cannot express."""

import pathlib
import tomllib

PYPROJECT = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"


def test_session_extra_installs_itsdangerous_and_does_not_cap_starlette():
    extras = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["optional-dependencies"]
    assert extras["session"] == ["itsdangerous"]
