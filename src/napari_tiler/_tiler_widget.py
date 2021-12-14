"""
This provides the widgets to make or merge tiles
"""
from enum import Enum

import numpy as np
from magicgui import magic_factory
from napari.layers import Image
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
from tiler import Tiler

# TODO
# How can we access `TILING_MODES` descriptions written in Tiler class?
# Draw grid lines where tiles would be

##### CLASS IMPLEMENTATION #####
class TilerWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()

        self.viewer = napari_viewer
        mode_comboBox = QComboBox()
        mode_comboBox.addItems(Tiler.TILING_MODES)

        layout = QVBoxLayout()
        layout.addWidget(mode_comboBox)

        self.setLayout(layout)


##### FUNCTION IMPLEMENTATION #####
class TilingMode(Enum):
    constant = "constant"
    drop = "drop"
    irregular = "irregular"
    reflect = "reflect"
    edge = "edge"
    wrap = "wrap"


@magic_factory(
    img_layer={"label": "Input Image"},
    tile_shape_x={"label": "Tile Width"},
    tile_shape_y={"label": "Tile Height"},
    overlap={"label": "Overlap", "tooltip": "Specifies overlap between tiles"},
    mode={"label": "Mode", "tooltip": "Tiling mode"},
    constant_value={
        "label": "Constant",
        "tooltip": "Specifies the value of padding when using constant mode",
    },
)
def make_tiles(
    img_layer: "napari.layers.Image",
    tile_shape_x: int = 128,
    tile_shape_y: int = 128,
    overlap: float = 0.1,
    mode: TilingMode = TilingMode.constant,
    constant_value: float = 0.0,
) -> "napari.layers.Image":
    data_shape = img_layer.data.shape
    tile_shape = [tile_shape_x, tile_shape_y]
    print(tile_shape)
    mode = mode.value
    if overlap == int(overlap):
        overlap = int(overlap)
    if constant_value == int(constant_value):
        constant_value = int(constant_value)
    channel_dimension = None
    is_rgb = img_layer.rgb
    if is_rgb:
        tile_shape.append(data_shape[-1])  # rgb(a) is last dimension
        channel_dimension = len(data_shape) - 1
    # do 3D rgb(a) images exist?
    else:
        # match the rest of the tile dimensions with input dimensions
        for i in range(len(data_shape) - len(tile_shape)):
            tile_shape.insert(i, data_shape[i])  # x, y are last 2 dimensions
    tiler = Tiler(
        data_shape=data_shape,
        tile_shape=tile_shape,
        overlap=overlap,
        channel_dimension=channel_dimension,
        mode=mode,
        constant_value=constant_value,
    )
    num_tiles = len(tiler)
    tiles_stack = np.zeros((num_tiles, *tile_shape), dtype=img_layer.dtype)
    for i, tile in tiler.iterate(img_layer.data):
        tiles_stack[i, ...] = tile
    metadata = {
        "data_shape": data_shape,
        "tile_shape": tile_shape,
        "overlap": overlap,
        "channel_dimension": channel_dimension,
        "mode": mode,
        "constant_value": constant_value,
    }
    image_layer = Image(tiles_stack, rgb=is_rgb, metadata=metadata)

    return image_layer


if __name__ == "__main__":
    from napari import Viewer

    viewer = Viewer()
    viewer.open_sample("scikit-image", "cells3d")
    viewer.window.add_dock_widget(TilerWidget(viewer))
