"""
This provides the widgets to make or merge tiles
"""
from enum import Enum

from magicgui import magic_factory
from napari.layers import Image
from napari_plugin_engine import napari_hook_implementation
from napari_tools_menu import register_dock_widget
from qtpy.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from tiler import Merger, Tiler

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import napari

##### CLASS IMPLEMENTATION #####
# @register_dock_widget(menu="Utilities > Merger")
class MergerWidget(QWidget):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()

        self.viewer = viewer

        self.setLayout(QVBoxLayout())

        # add title
        title = QLabel("<b>Merge Tiles</b>")
        self.layout().addWidget(title)


##### FUNCTION IMPLEMENTATION #####
class WindowMode(Enum):
    boxcar = "boxcar"
    triang = "triang"
    blackman = "blackman"
    hamming = "hamming"
    hann = "hann"
    barlett = "bartlett"
    flattop = "flattop"
    parzen = "parzen"
    bohman = "bohman"
    blackmanharris = "blackmanharris"
    nuttall = "nuttall"
    barthann = "barthann"
    overlap_tile = "overlap-tile"


@magic_factory
def merge_tiles(
    img_layer: "napari.layers.Image",
    window: WindowMode = WindowMode.boxcar,
) -> "napari.layers.Image":
    window = window.value
    dtype = img_layer.dtype
    # check that the required metadata is available
    metadata = img_layer.metadata
    is_rgb = img_layer.rgb
    tiler = Tiler(
        data_shape=metadata["data_shape"],
        tile_shape=metadata["tile_shape"],
        overlap=metadata["overlap"],
        channel_dimension=metadata["channel_dimension"],
        mode=metadata["mode"],
        constant_value=metadata["constant_value"],
    )
    merger = Merger(
        tiler=tiler,
        window=window,
        logits=0,
    )
    num_tiles = img_layer.data.shape[0]
    for i in range(num_tiles):
        merger.add(i, img_layer.data[i, ...])
    merged_image = merger.merge()
    image_layer = Image(merged_image, rgb=is_rgb, metadata=metadata)

    return image_layer