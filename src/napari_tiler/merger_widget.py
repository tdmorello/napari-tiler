"""This provides the widgets to make or merge tiles."""
from typing import TYPE_CHECKING, Optional

from magicgui.widgets import create_widget
from napari_tools_menu import register_dock_widget
from qtpy.QtCore import QEvent
from qtpy.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from tiler import Merger, Tiler

if TYPE_CHECKING:
    import napari  # pragma: no cover


@register_dock_widget(menu="Utilities > Merger")
class MergerWidget(QWidget):
    """A class for the Merger widget."""

    def __init__(self, viewer: "napari.viewer.Viewer") -> None:
        """Init the merger class."""
        super().__init__()
        # create main layout
        self.viewer = viewer
        self.setLayout(QVBoxLayout())
        # add title
        title = QLabel("<b>Merge Tiles</b>")
        self.layout().addWidget(title)

        # TODO only display image and labels layers
        self.layer_select = create_widget(
            annotation="napari.layers.Layer", label="image_layer"
        )
        # mode selection
        self.mode_select = QComboBox()
        self.mode_select.addItems(Merger.SUPPORTED_WINDOWS)
        # add form to main layout
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.addRow("Image", self.layer_select.native)
        form_layout.addRow("Mode", self.mode_select)
        self.layout().addLayout(form_layout)
        # `run` button
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        self.layout().addWidget(self.run_btn)

    def _initialize_merger(self) -> None:
        image = self.layer_select.value
        if image is None:
            raise ValueError("No image data available.")

        layer = self.layer_select.value
        metadata = layer.metadata
        try:
            tiler = Tiler(
                data_shape=metadata["data_shape"],
                tile_shape=metadata["tile_shape"],
                overlap=metadata["overlap"],
                channel_dimension=metadata["channel_dimension"],
                mode=metadata["mode"],
                constant_value=metadata["constant_value"],
            )
        except KeyError:
            raise ValueError(
                "Could not initialize `Merger`. Check that the layer metadata "
                "contains the proper arguments for `Tiler` initialization."
            )
        self._merger = Merger(
            tiler=tiler, window=self.mode_select.currentText()
        )

    def _run(self) -> None:
        self._initialize_merger()
        merger = self._merger
        image = self.layer_select.value
        layer_data, layer_meta, layer_type = image.as_layer_data_tuple()
        layer_meta["name"] = layer_meta["name"] + " (merged)"
        num_tiles = layer_data.shape[0]
        for i in range(num_tiles):
            merger.add(i, image.data[i, ...])
        merged = merger.merge(dtype=image.dtype)
        # FIXME better way to handle differences in input/output dimensions?
        for t in ["rotate", "scale", "shear", "translate"]:
            del layer_meta[t]
        self.viewer._add_layer_from_data(merged, layer_meta, layer_type)

    # thanks to https://github.com/BiAPoL/napari-clusters-plotter/blob/main/napari_clusters_plotter/_measure.py  # noqa
    def showEvent(self, event: QEvent) -> None:  # noqa: D102
        super().showEvent(event)
        self.reset_choices()

    def reset_choices(self, event: Optional[QEvent] = None) -> None:
        """Repopulate image list."""
        self.layer_select.reset_choices(event)
