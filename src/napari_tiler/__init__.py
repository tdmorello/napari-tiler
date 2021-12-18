"""Napari plugin for tiling."""
try:
    from importlib.metadata import (  # type: ignore
        PackageNotFoundError,
        version,
    )
except ImportError:  # pragma: no cover
    from importlib_metadata import (  # type: ignore
        PackageNotFoundError,
        version,
    )


try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"


from ._dock_widget import napari_experimental_provide_dock_widget  # noqa: F401
