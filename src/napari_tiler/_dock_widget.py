"""
This provides the widgets to make or merge tiles
"""
from napari_plugin_engine import napari_hook_implementation

from ._merger_widget import merge_tiles
from ._tiler_widget import make_tiles, TilerWidget


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [TilerWidget, make_tiles, merge_tiles]
    # return [TilerWidget, make_tiles]
