"""This provides the widget to make tiles."""

import logging
from typing import TYPE_CHECKING, Dict, Optional

import numpy as np
from magicgui.widgets import create_widget
from napari_tools_menu import register_dock_widget
from qtpy.QtCore import QEvent
from qtpy.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from tiler import Tiler

if TYPE_CHECKING:
    import napari  # pragma: no cover

from .components.tile_dimensions import DimensionsInput

logger = logging.getLogger(__name__)


class DEFAULTS:
    """Default parameters for gui."""

    tile_size = 128
    extra_dim_size = 5
    overlap = 0.1


@register_dock_widget(menu="Utilities > Tiler")
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

        # layer selection
        # TODO only display image and labels layers
        self.layer_select = create_widget(
            annotation="napari.layers.Layer", label="image_layer"
        )
        self.layer_select.native.currentIndexChanged.connect(self._on_layer_select)

        # tile dimensions input
        self.tile_dims_container = DimensionsInput()
        self.tile_dims_container.valueChanged.connect(self._parameters_changed)

        # overlap input
        self.overlap_dsb = QDoubleSpinBox()
        self.overlap_dsb.setValue(DEFAULTS.overlap)
        self.overlap_dsb.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        # NOTE: `editingFinished` could be useful to prevent updating while
        # still entering input
        # self.overlap_dsb.editingFinished.connect(self._validate_overlap_value)
        # self.overlap_dsb.editingFinished.connect(self._parameters_changed)
        self.overlap_dsb.valueChanged.connect(self._validate_overlap_value)
        self.overlap_dsb.valueChanged.connect(self._parameters_changed)

        # mode selection
        self.mode_select = QComboBox()
        # Dec 2021: "irregular" mode is unsupported
        available_modes = Tiler.TILING_MODES.copy()
        available_modes.remove("irregular")
        self.mode_select.addItems(available_modes)
        self.mode_select.currentIndexChanged.connect(self._on_mode_select)

        # `constant` value input
        self.constant_dsb = QDoubleSpinBox(minimum=0, maximum=255)
        self.constant_lbl = QLabel("Constant")
        # keep track of `constant`

        # `preview` toggle
        self.preview_layout = QHBoxLayout()
        self.preview_chkb = QCheckBox()
        self.preview_chkb.stateChanged.connect(self._parameters_changed)
        self.preview_shape = QLabel()
        self.preview_layout.addWidget(self.preview_chkb)
        self.preview_layout.addWidget(self.preview_shape)

        # add form to main layout
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.addRow("Image", self.layer_select.native)
        form_layout.addRow("Tile Size", self.tile_dims_container)
        form_layout.addRow("Overlap", self.overlap_dsb)
        form_layout.addRow("Mode", self.mode_select)
        form_layout.addRow(self.constant_lbl, self.constant_dsb)
        # form_layout.addRow(self.constant_dsb_container)
        form_layout.addRow("Preview", self.preview_layout)
        self.layout().addLayout(form_layout)
        # `run` button
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        self.layout().addWidget(self.run_btn)

        # initial show or hide constant input spinbox
        self._on_mode_select()
        self._parameters_changed()

    def _on_layer_select(self) -> None:
        try:
            # self.tile_dims_container._max_ndims = self.layer_select.value.ndim
            ...
        except AttributeError:
            pass

    def _on_mode_select(self) -> None:
        if self.mode_select.currentText() == "constant":
            self.constant_dsb.show()
            self.constant_lbl.show()
        else:
            self.constant_dsb.hide()
            self.constant_lbl.hide()

    @property
    def tile_shape(self) -> np.ndarray:
        """Returns entered dimensions reordered for napari axis order."""
        shape = self.tile_dims_container.dims
        # Move X and Y dimensions to the end, keep the rest in order
        return np.concatenate([shape[2:], shape[[0, 1]]])

    def _initialize_tiler(self) -> Dict:
        layer = self.layer_select.value
        if layer is None:
            raise ValueError("No image data available.")

        data_shape = np.array(layer.data.shape)
        tile_shape = self.tile_shape
        mode = self.mode_select.currentText()
        constant = self.constant_dsb.value()
        overlap = self.overlap_dsb.value()
        if overlap == int(overlap):
            overlap = int(overlap)

        # Validate and adjust tile shape
        channel_dimension = None
        is_rgb = layer.rgb
        if is_rgb:
            # RGB(A) is the last dimension, could be 3 or 4
            tile_shape = np.append(tile_shape, data_shape[-1])
            channel_dimension = len(data_shape) - 1

        elif len(data_shape) >= len(tile_shape):
            for i in range(len(data_shape) - len(tile_shape)):
                tile_shape = np.insert(tile_shape, i, data_shape[i])

        else:
            raise ValueError(
                "Tiles must have the same or fewer dimensions than the "
                f"image. Tiles have {len(tile_shape)} dimenions and the "
                f"image has {len(data_shape)} dimensions."
            )

        kwargs = {
            "data_shape": data_shape,
            "tile_shape": tile_shape,
            "overlap": overlap,
            "channel_dimension": channel_dimension,
            "mode": mode,
            "constant_value": constant,
        }

        self._tiler = Tiler(**kwargs)

        return kwargs

    def _run(self) -> None:
        metadata = self._initialize_tiler()
        tiler = self._tiler
        layer = self.layer_select.value
        is_rgb = layer.rgb

        tiles_stack = tiler.get_all_tiles(layer.data).astype(layer.dtype)

        self.viewer.add_image(
            tiles_stack,
            name=f"{layer.name} tiles",
            rgb=is_rgb,
            metadata=metadata,
            colormap=layer.colormap,
        )

    def _parameters_changed(self) -> None:
        # TODO wait until user has completed input, otherwise this is costly
        if self.preview_chkb.isChecked():
            self._initialize_tiler()
            self.preview_shape.setText(str(self._tiler.get_mosaic_shape()))
            self._update_preview_layer()
        else:
            self._remove_preview_layer()
            self.preview_shape.setText("")

    def _validate_overlap_value(self) -> None:
        value = self.overlap_dsb.value()
        if value >= 1:
            self.overlap_dsb.setValue(int(value))

    def _update_preview_layer(self) -> None:
        """Generate a shapes layer to display tiles preview."""
        tiles = []
        for tile_id in range(len(self._tiler)):
            bbox = np.array(self._tiler.get_tile_bbox(tile_id))
            # only grab last 2 dimensions of bbox
            bbox = bbox[..., [-2, -1]]
            tiles.append(bbox)

        # TODO do not switch layer selection
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

        # move preview layer to front
        layers = self.viewer.layers
        idx = layers.index(self._preview_layer)
        layers.move_selected(idx, -1)

    def _remove_preview_layer(self) -> None:
        if "tiler preview" in self.viewer.layers:
            self.viewer.layers.remove("tiler preview")

    # thanks to https://github.com/BiAPoL/napari-clusters-plotter/blob/main/napari_clusters_plotter/_measure.py  # noqa
    def showEvent(self, event: QEvent) -> None:  # noqa: D102
        super().showEvent(event)
        self.reset_choices()

    def reset_choices(self, event: Optional[QEvent] = None) -> None:
        """Repopulate image list."""
        self.layer_select.reset_choices(event)
