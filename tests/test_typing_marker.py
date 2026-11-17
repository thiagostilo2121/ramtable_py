"""Tests for the PEP 561 typing marker and packaging metadata."""

import tomllib
from importlib.resources import files
from pathlib import Path


def test_package_includes_the_py_typed_marker():
    marker = files("ramtable").joinpath("py.typed")

    assert marker.is_file()


def test_project_declares_the_typed_classifier():
    project_file = Path(__file__).parents[1] / "pyproject.toml"
    project = tomllib.loads(project_file.read_text(encoding="utf-8"))

    assert "Typing :: Typed" in project["project"]["classifiers"]
