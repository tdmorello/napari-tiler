import napari_tiler
import pytest
import numpy as np
from napari.layers import Image

# this is your plugin name declared in your napari.plugins entry point
MY_PLUGIN_NAME = "napari-tiler"
# the name of your widget(s)
MY_WIDGET_NAMES = ["Tiler Widget"]


@pytest.mark.parametrize("widget_name", MY_WIDGET_NAMES)
def test_something_with_viewer(widget_name, make_napari_viewer, napari_plugin_manager):
    napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
    viewer = make_napari_viewer()
    num_dw = len(viewer.window._dock_widgets)
    viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name=widget_name
    )
    assert len(viewer.window._dock_widgets) == num_dw + 1


@pytest.mark.parametrize(
    "image_data,rgb",
    [
        (np.random.random((512, 512)), False),
        (np.random.random((5, 512, 512)), False),
        (np.random.random((512, 512, 3)), True),
    ],
)
def test_tiler_widget(image_data, rgb, make_napari_viewer, napari_plugin_manager):
    napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
    viewer = make_napari_viewer()
    _, widget = viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name="Tiler Widget"
    )
    viewer.add_image(image_data, rgb=rgb)
    num_layers = len(viewer.layers)
    widget._run()
    assert len(viewer.layers) == num_layers + 1


# TODO migrate this test functino with the above?
def test_generate_preview(make_napari_viewer, napari_plugin_manager):
    napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
    viewer = make_napari_viewer()
    _, widget = viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name="Tiler Widget"
    )
    image = viewer.add_image(np.random.random((512, 512)))
    num_layers = len(viewer.layers)
    widget.preview_chkb.setChecked(True)
    assert len(viewer.layers) == num_layers + 1
    widget.preview_chkb.setChecked(False)
    assert len(viewer.layers) == num_layers


# def test_merger_widget():
#     pass
