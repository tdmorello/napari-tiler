"""This provides the widget to make tiles."""

from typing import TYPE_CHECKING, Dict, Optional

import numpy as np
from magicgui.widgets import create_widget
from qtpy.QtCore import QEvent

# from napari_tools_menu import register_dock_widget
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from tiler import Tiler

if TYPE_CHECKING:
    import napari  # pragma: no cover

# TODO add logging


# FIXME register dock widget to tool menu
# TODO equal widget widths in qformlayout?
# TODO abstract to a "base" class that defines methods `showEvent` and `reset_choices`  # noqa
# @register_dock_widget(menu="Utilities > Tiler")
class TilerWidget(QWidget):
    """The main Tiler widget."""

    def __init__(self, viewer: "napari.viewer.Viewer") -> None:
        """Init the Tiler widget."""
        super().__init__()

        self.viewer = viewer
        self.setLayout(QVBoxLayout())
        # add title
        title = QLabel("<b>Make Tiles</b>")
        self.layout().addWidget(title)
        # image selection
        self.image_select = create_widget(
            annotation="napari.layers.Image", label="image_layer"
        )
        # tile size input
        tile_size_container = QWidget()
        tile_size_container.setLayout(QHBoxLayout())
        tile_size_container.layout().setContentsMargins(0, 0, 0, 0)
        # TODO set maximum based on input image size
        self.tile_size_x_sb = QSpinBox(minimum=0, maximum=10000)
        self.tile_size_y_sb = QSpinBox(minimum=0, maximum=10000)
        self.tile_size_x_sb.setValue(128)
        self.tile_size_y_sb.setValue(128)
        self.tile_size_x_sb.valueChanged.connect(self._parameters_changed)
        self.tile_size_y_sb.valueChanged.connect(self._parameters_changed)
        tile_size_container.layout().addWidget(self.tile_size_x_sb)
        tile_size_container.layout().addWidget(QLabel("×"))
        tile_size_container.layout().addWidget(self.tile_size_y_sb)
        # overlap input
        self.overlap_dsb = QDoubleSpinBox()
        self.overlap_dsb.setValue(0.1)
        self.overlap_dsb.valueChanged.connect(self._validate_overlap_value)
        self.overlap_dsb.valueChanged.connect(self._parameters_changed)
        # mode selection
        self.mode_select = QComboBox()
        self.mode_select.addItems(Tiler.TILING_MODES)
        # `constant` value input
        self.constant_dsb = QDoubleSpinBox()
        # `preview` toggle
        self.preview_chkb = QCheckBox()
        self.preview_chkb.stateChanged.connect(self._parameters_changed)
        # add form to main layout
        form_layout = QFormLayout()
        form_layout.addRow("Image", self.image_select.native)
        form_layout.addRow("Tile Size", tile_size_container)
        form_layout.addRow("Overlap", self.overlap_dsb)
        form_layout.addRow("Mode", self.mode_select)
        form_layout.addRow("Constant", self.constant_dsb)
        form_layout.addRow("Preview", self.preview_chkb)
        self.layout().addLayout(form_layout)
        # `run` button
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        self.layout().addWidget(self.run_btn)

    def _initialize_tiler(self) -> Dict:
        image = self.image_select.value
        data_shape = image.data.shape
        tile_shape = [self.tile_size_x_sb.value(), self.tile_size_y_sb.value()]
        overlap = self.overlap_dsb.value()
        if overlap == int(overlap):
            overlap = int(overlap)
        mode = self.mode_select.currentText()
        constant = self.constant_dsb.value()
        if constant == int(constant):
            constant = int(constant)
        channel_dimension = None

        # make sure tile shape is appropriate for Tiler class
        is_rgb = image.rgb
        if is_rgb:
            tile_shape.append(data_shape[-1])  # rgb(a) is last dimension
            channel_dimension = len(data_shape) - 1
        else:
            for i in range(len(data_shape) - len(tile_shape)):
                # x, y should be last 2 dimensions
                tile_shape.insert(i, data_shape[i])

        self._tiler = Tiler(
            data_shape=data_shape,
            tile_shape=tile_shape,
            overlap=overlap,
            channel_dimension=channel_dimension,
            mode=mode,
            constant_value=constant,
        )

        # TODO change to object property
        metadata = {
            "data_shape": data_shape,
            "tile_shape": tile_shape,
            "overlap": overlap,
            "channel_dimension": channel_dimension,
            "mode": mode,
            "constant_value": constant,
        }

        return metadata

    def _run(self) -> None:
        # TODO copy over other image data like transform, colormap, ...
        metadata = self._initialize_tiler()
        tiler = self._tiler
        image = self.image_select.value
        # move parameters to class?
        tile_shape = metadata["tile_shape"]
        is_rgb = image.rgb

        tiles_stack = np.zeros((len(tiler), *tile_shape), dtype=image.dtype)
        for i, tile in tiler.iterate(image.data):
            tiles_stack[i, ...] = tile

        # TODO include all settable image layer attributes
        self.viewer.add_image(
            tiles_stack,
            name=f"{image.name} tiles",
            rgb=is_rgb,
            metadata=metadata,
            colormap=image.colormap,
        )

    def _validate_overlap_value(self) -> None:
        value = self.overlap_dsb.value()
        if value >= 1:
            self.overlap_dsb.setValue(int(value))

    def _parameters_changed(self) -> None:
        # FIXME wait until user has completed input, otherwise this is costly
        if self.preview_chkb.isChecked():
            self._generate_preview_layer()
        else:
            self._remove_preview_layer()

    # def _match_tile_shape(self):
    #     """Output proper tile shape for Tiler class"""
    #     pass

    def _generate_preview_layer(self) -> None:
        """Generate a shapes layer to display tiles preview."""
        self._initialize_tiler()
        tiles = []
        for tile_id in range(len(self._tiler)):
            bbox = np.array(self._tiler.get_tile_bbox_position(tile_id))
            # only grab last 2 dimensions of bbox
            bbox = bbox[..., [-2, -1]]
            tiles.append(bbox)

        if not ("tiler preview" in self.viewer.layers):
            self._preview_layer = self.viewer.add_shapes(name="tiler preview")
        else:
            self._preview_layer.data = []

        self._preview_layer.add_rectangles(
            tiles,
            # set bbox display options
            edge_width=5,
            edge_color="white",
            face_color="#ffffff20",
        )

        # # FIXME this emits a warning
        # # TypeError: "layers" has allow_mutation set to False and cannot be assigned  # noqa
        # # move preview layer to front
        # layers = self.viewer.layers
        # idx = layers.index(self._preview_layer)
        # self.viewer.layers += [layers.pop(idx)]

    def _remove_preview_layer(self) -> None:
        if "tiler preview" in self.viewer.layers:
            self.viewer.layers.remove("tiler preview")

    # thanks to https://github.com/BiAPoL/napari-clusters-plotter/blob/main/napari_clusters_plotter/_measure.py  # noqa
    def showEvent(self, event: QEvent) -> None:  # noqa: D102
        super().showEvent(event)
        self.reset_choices()

    def reset_choices(self, event: Optional[QEvent] = None) -> None:
        """Repopulate image list."""
        self.image_select.reset_choices(event)


# if __name__ == "__main__":
#     from napari import Viewer

#     viewer = Viewer()
#     viewer.open_sample("scikit-image", "cells3d")
#     viewer.window.add_dock_widget(TilerWidget(viewer))
