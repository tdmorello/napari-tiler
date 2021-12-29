"""This provides the widget to make tiles."""

import logging
from typing import TYPE_CHECKING, Dict, Optional

import numpy as np
from magicgui.widgets import create_widget
from napari_tools_menu import register_dock_widget
from qtpy.QtCore import QEvent, Signal
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


logger = logging.getLogger(__name__)


class DEFAULTS:
    """Default parameters for gui."""

    tile_size = 128
    extra_dim_size = 5
    overlap = 0.1


@register_dock_widget(menu="Utilities > Tiler")
class TilerWidget(QWidget):
    """The main Tiler widget."""

    def __init__(self, napari_viewer: "napari.viewer.Viewer") -> None:
        """Init the Tiler widget."""
        super().__init__()

        self.viewer = napari_viewer
        self.setLayout(QVBoxLayout())

        # add title
        title = QLabel("<b>Make Tiles</b>")
        self.layout().addWidget(title)

        # image selection
        self.image_select = create_widget(
            annotation="napari.layers.Image", label="image_layer"
        )

        # tile dimensions input
        self.tile_dims_container = TileDimensions()
        self.tile_dims_container.valueChanged.connect(self._parameters_changed)

        # overlap input
        self.overlap_dsb = QDoubleSpinBox()
        self.overlap_dsb.setValue(DEFAULTS.overlap)
        self.overlap_dsb.valueChanged.connect(self._validate_overlap_value)
        self.overlap_dsb.valueChanged.connect(self._parameters_changed)

        # mode selection
        self.mode_select = QComboBox()
        self.mode_select.addItems(Tiler.TILING_MODES)
        self.mode_select.currentIndexChanged.connect(self._on_mode_changed)

        # `constant` value input
        self.constant_dsb = QDoubleSpinBox(minimum=0, maximum=255)
        self.constant_lbl = QLabel("Constant")

        # `preview` toggle
        self.preview_chkb = QCheckBox()
        self.preview_chkb.stateChanged.connect(self._parameters_changed)

        # add form to main layout
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.addRow("Image", self.image_select.native)
        form_layout.addRow("Tile Size", self.tile_dims_container)
        form_layout.addRow("Overlap", self.overlap_dsb)
        form_layout.addRow("Mode", self.mode_select)
        form_layout.addRow(self.constant_lbl, self.constant_dsb)
        # form_layout.addRow(self.constant_dsb_container)
        form_layout.addRow("Preview", self.preview_chkb)
        self.layout().addLayout(form_layout)
        # `run` button
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        self.layout().addWidget(self.run_btn)

        # initial show or hide constant input spinbox
        self._on_mode_changed()
        self._parameters_changed()

    def _on_mode_changed(self) -> None:
        if self.mode_select.currentText() == "constant":
            self.constant_dsb.show()
            self.constant_lbl.show()
        else:
            self.constant_dsb.hide()
            self.constant_lbl.hide()

    @property
    def tile_shape(self) -> np.ndarray:
        """Returns tile dimensions reordered to fit napari convention."""
        shape = self.tile_dims_container.get_dims()
        # Move X and Y dimensions to the end, keep the rest in order
        return np.concatenate([shape[2:], shape[[0, 1]]])

    def _initialize_tiler(self) -> Dict:
        image = self.image_select.value  # NOTE add if not none?
        if image is None:
            raise ValueError("No image data available.")

        data_shape = np.array(image.data.shape)
        tile_shape = self.tile_shape
        mode = self.mode_select.currentText()
        constant = self.constant_dsb.value()
        overlap = self.overlap_dsb.value()
        if overlap == int(overlap):
            overlap = int(overlap)

        # Validate and adjust tile shape
        channel_dimension = None
        is_rgb = image.rgb
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
        image = self.image_select.value
        # move parameters to class?
        tile_shape = metadata["tile_shape"]
        is_rgb = image.rgb

        tiles_stack = np.zeros((len(tiler), *tile_shape), dtype=image.dtype)
        for i, tile in tiler.iterate(image.data):
            tiles_stack[i, ...] = tile

        self.viewer.add_image(
            tiles_stack,
            name=f"{image.name} tiles",
            rgb=is_rgb,
            metadata=metadata,
            colormap=image.colormap,
        )

    def _parameters_changed(self) -> None:
        # TODO wait until user has completed input, otherwise this is costly
        if self.preview_chkb.isChecked():
            self._initialize_tiler()
            self._update_preview_layer()
        else:
            self._remove_preview_layer()

    def _validate_overlap_value(self) -> None:
        value = self.overlap_dsb.value()
        if value >= 1:
            self.overlap_dsb.setValue(int(value))

    def _update_preview_layer(self) -> None:
        """Generate a shapes layer to display tiles preview."""
        tiles = []
        for tile_id in range(len(self._tiler)):
            bbox = np.array(self._tiler.get_tile_bbox_position(tile_id))
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
        self.image_select.reset_choices(event)


class DimensionField(QWidget):
    """Base class for dimension input fields."""

    def __init__(self) -> None:
        """Init DimensionField class."""
        super().__init__()
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self._del_btn = QPushButton("⊖")
        self._del_btn.clicked.connect(self._remove)
        self._add_btn = QPushButton("⊕")
        self._add_btn.clicked.connect(self._add_below)

    def _remove(self) -> None:
        """Remove self from layout and delete."""
        self.setParent(None)
        del self

    def _add_below(self) -> None:
        parent_layout: QVBoxLayout = self.parent().layout()
        idx = parent_layout.indexOf(self)
        parent_layout.insertWidget(idx + 1, ExtraDimensionField())

    def get_dims(self) -> np.ndarray:
        """Return dimension(s) from input field(s)."""
        dims = np.array([], dtype=int)
        layout = self.layout()
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QSpinBox):
                dims = np.append(dims, widget.value())
        return dims


class XYDimensionField(DimensionField):
    """Dimension input for X and Y sizes."""

    valueChanged = Signal()

    def __init__(self) -> None:
        """Init XYDimensionField class."""
        super().__init__()
        self._x_dim_sb = QSpinBox(minimum=0, maximum=10000)
        self._x_dim_sb.setValue(DEFAULTS.tile_size)
        self._x_dim_sb.valueChanged.connect(self.valueChanged)
        self._y_dim_sb = QSpinBox(minimum=0, maximum=10000)
        self._y_dim_sb.setValue(DEFAULTS.tile_size)
        self._y_dim_sb.valueChanged.connect(self.valueChanged)

        self.layout().addWidget(self._x_dim_sb)
        self.layout().addWidget(QLabel("×"))
        self.layout().addWidget(self._y_dim_sb)
        self.layout().addWidget(self._add_btn)


class ExtraDimensionField(DimensionField):
    """Dimension input for an extra dimension (e.g. Z, T, ...)."""

    valueChanged = Signal()

    def __init__(self) -> None:
        """Init ExtraDimensionField class."""
        super().__init__()

        self._dim_sb = QSpinBox(minimum=0, maximum=10000)
        self._dim_sb.setValue(DEFAULTS.extra_dim_size)
        self._dim_sb.valueChanged.connect(self.valueChanged)

        layout = self.layout()
        layout.addWidget(QLabel("×"))
        layout.addWidget(self._dim_sb)
        layout.addWidget(self._del_btn)
        layout.addWidget(self._add_btn)


class TileDimensions(QWidget):
    """A container for tile dimensions input."""

    valueChanged = Signal()

    def __init__(self) -> None:
        """Init the TileDimensions class."""
        super().__init__()

        xy_dims_field = XYDimensionField()
        xy_dims_field.valueChanged.connect(self.valueChanged)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(xy_dims_field)

    def get_dims(self) -> np.ndarray:
        """Return an array in the order of input fields."""
        dims = np.array([], dtype=int)
        layout = self.layout()

        for i in range(layout.count()):
            field = layout.itemAt(i)
            dims = np.append(dims, field.widget().get_dims())
        return np.array(dims).flatten()


if __name__ == "__main__":
    from napari import Viewer

    viewer = Viewer()
    viewer.open_sample("scikit-image", "cells3d")
    tiler_widget = TilerWidget(viewer)
    viewer.window.add_dock_widget(tiler_widget)
