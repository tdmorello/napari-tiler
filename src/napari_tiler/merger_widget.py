"""
This provides the widgets to make or merge tiles
"""
from typing import TYPE_CHECKING, Optional

from magicgui.widgets import create_widget
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


# @register_dock_widget(menu="Utilities > Merger")
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
        # image selection
        self.image_select = create_widget(
            annotation="napari.layers.Image", label="image_layer"
        )
        # mode selection
        self.mode_select = QComboBox()
        self.mode_select.addItems(Merger.SUPPORTED_WINDOWS)
        # add form to main layout
        form_layout = QFormLayout()
        form_layout.addRow("Image", self.image_select.native)
        form_layout.addRow("Mode", self.mode_select)
        self.layout().addLayout(form_layout)
        # `run` button
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        self.layout().addWidget(self.run_btn)

    def _initialize_merger(self) -> None:
        image = self.image_select.value
        metadata = image.metadata
        print(metadata)
        # is_rgb = image.rgb
        tiler = Tiler(
            data_shape=metadata["data_shape"],
            tile_shape=metadata["tile_shape"],
            overlap=metadata["overlap"],
            channel_dimension=metadata["channel_dimension"],
            mode=metadata["mode"],
            constant_value=metadata["constant_value"],
        )
        self._merger = Merger(
            tiler=tiler, window=self.mode_select.currentText()
        )

    def _run(self) -> None:
        # TODO copy over other image data like transform, colormap, ...
        self._initialize_merger()
        merger = self._merger
        image = self.image_select.value
        metadata = image.metadata
        is_rgb = image.rgb
        num_tiles = image.data.shape[0]
        for i in range(num_tiles):
            merger.add(i, image.data[i, ...])
        merged = merger.merge(dtype=image.dtype)
        self.viewer.add_image(
            merged,
            name=f"{image.name} merged",
            rgb=is_rgb,
            metadata=metadata,
            colormap=image.colormap,
        )

    # thanks to https://github.com/BiAPoL/napari-clusters-plotter/blob/main/napari_clusters_plotter/_measure.py  # noqa
    def showEvent(self, event: QEvent) -> None:  # noqa: D102
        super().showEvent(event)
        self.reset_choices()

    def reset_choices(self, event=Optional[QEvent]):
        """Repopulate image list."""
        self.image_select.reset_choices(event)


# if __name__ == "__main__":
#     from napari import Viewer

#     from napari_tiler.tiler_widget import TilerWidget

#     viewer = Viewer()
#     viewer.open_sample("scikit-image", "cell")
#     viewer.window.add_dock_widget(TilerWidget(viewer))
#     viewer.window.add_dock_widget(MergerWidget(viewer))
