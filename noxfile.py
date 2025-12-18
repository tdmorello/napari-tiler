"""Nox sessions."""
import sys
import tempfile

import nox
from nox.sessions import Session

python_versions = ["3.10", "3.11", "3.12"]


@nox.session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    _install_via_pip(session)

    session.install("napari[all]", "pytest>=7.0", "pytest-cov", "pytest-qt")
    if sys.platform == "linux":
        session.install("pytest-xvfb")

    session.run("pytest")


@nox.session
def lint(session: Session) -> None:
    """Run linting."""
    pass


def _install_via_pip(session: Session) -> None:
    with tempfile.NamedTemporaryFile() as requirements:
        if sys.platform == "win32":
            requirements_path = "requirements.txt"
        else:
            requirements_path = requirements.name
        session.run(
            "poetry",
            "export",
            "--without-hashes",
            "-o",
            requirements_path,
            external=True,
        )
        session.install("-r", requirements_path)
