"""This provides the widgets to make or merge tiles."""
from napari_plugin_engine import napari_hook_implementation

from .merger_widget import MergerWidget
from .tiler_widget import TilerWidget


@napari_hook_implementation
def napari_experimental_provide_dock_widget() -> list:  # noqa: D103
    return [TilerWidget, MergerWidget]
