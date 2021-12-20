"""Nox sessions."""
import sys
import tempfile

import nox
from nox.sessions import Session

python_versions = ["3.7", "3.8", "3.9", "3.10"]


@nox.session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--without-hashes",
            "-o",
            requirements.name,
            external=True,
        )
        session.install("-r", requirements.name)

    session.install("napari[all]", "pytest", "pytest-cov", "pytest-qt")
    if sys.platform == "linux":
        session.install("pytest-xvfb")

    session.run("pytest")


@nox.session
def lint(session: Session) -> None:
    """Run linting."""
    pass
