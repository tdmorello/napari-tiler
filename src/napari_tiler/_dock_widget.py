"""
This provides the widgets to make or merge tiles
"""
from enum import Enum

import numpy as np
from magicgui import magic_factory
from napari.layers import Image
from napari_plugin_engine import napari_hook_implementation
from tiler import Tiler, Merger

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


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [make_tiles, merge_tiles]


if __name__ == "__main__":
    from napari import Viewer

    viewer = Viewer()
    viewer.open_sample("scikit-image", "cells3d")
    # viewer.open_sample("scikit-image", "astronaut")
    viewer.window.add_plugin_dock_widget(
        plugin_name="napari-tiler", widget_name="make_tiles"
    )
    viewer.window.add_plugin_dock_widget(
        plugin_name="napari-tiler", widget_name="merge_tiles"
    )
