"""Nox sessions."""
import nox
from nox.sessions import Session


@nox.session(python=["3.7", "3.8", "3.9", "3.10"])
def tests(session: Session) -> None:
    """Run tests."""
    session.run("poetry", "install", "--no-dev", external=True)
    session.run("pytest")


@nox.session
def lint(session: Session) -> None:
    """Run linting."""
    pass
