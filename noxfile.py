"""Nox sessions."""
import sys

import nox
from nox.sessions import Session

python_versions = ["3.7", "3.8", "3.9", "3.10"]


@nox.session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    session.run("poetry", "install", "--no-dev", external=True)
    # Test requirements will hopefully be moved to pyproject.toml in a
    # 'testing' extras
    # session.run("poetry", "install", "--extras='testing", external=True)
    session.install("napari", "pytest", "pytest-qt")
    if sys.platform == "linux":
        session.install("pytest-xvfb")
    session.run("pytest")


@nox.session
def lint(session: Session) -> None:
    """Run linting."""
    pass
