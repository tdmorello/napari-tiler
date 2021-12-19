"""Nox sessions."""
import tempfile
from typing import Any

import nox
from nox.sessions import Session


# https://github.com/cjolowicz/hypermodern-python/blob/master/noxfile.py
def install_with_constraints(
    session: Session, *args: str, **kwargs: Any
) -> None:
    """Install packages constrained by Poetry's lock file.

    This function is a wrapper for nox.sessions.Session.install. It
    invokes pip to install packages inside of the session's virtualenv.
    Additionally, pip is passed a constraints file generated from
    Poetry's lock file, to ensure that the packages are pinned to the
    versions specified in poetry.lock. This allows you to manage the
    packages as Poetry development dependencies.

    Arguments:
        session: The Session object.
        args: Command-line arguments for pip.
        kwargs: Additional keyword arguments for Session.install.
    """
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--requirement={requirements.name}", *args, **kwargs)


@nox.session(python=["3.7", "3.8", "3.9", "3.10"])
def tests(session: Session) -> None:
    """Run the test suite."""
    session.run("poetry", "install", external=True)
    # install_with_constraints(session, "pytest", "pytest-cov", "pytest-qt")
    session.run("python", "-V")
    session.run("pytest", external=True)


@nox.session
def lint(session: Session) -> None:
    """Run linting."""
    pass
