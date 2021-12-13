"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
from enum import Enum

import numpy as np
from magicgui import magic_factory
from napari.layers import Image
from napari_plugin_engine import napari_hook_implementation
from tiler import Tiler

# TODO
# How can we access `TILING_MODES` descriptions written in Tiler class?
# Draw grid lines where tiles would be


class TilingMode(Enum):
    constant = "constant"
    drop = "drop"
    irregular = "irregular"
    reflect = "reflect"
    edge = "edge"
    wrap = "wrap"


@magic_factory
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


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [make_tiles]
