import numpy as np
import pytest

import napari_tiler

# this is your plugin name declared in your napari.plugins entry point
MY_PLUGIN_NAME = "napari-tiler"
# the name of your widget(s)
MY_WIDGET_NAMES = ["Tiler Widget"]


@pytest.mark.parametrize("widget_name", MY_WIDGET_NAMES)
def test_something_with_viewer(
    widget_name, make_napari_viewer, napari_plugin_manager
):
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
def test_tiler_widget(
    image_data, rgb, make_napari_viewer, napari_plugin_manager
):
    napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
    viewer = make_napari_viewer()
    _, widget = viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name="Tiler Widget"
    )
    viewer.add_image(image_data, rgb=rgb)
    num_layers = len(viewer.layers)
    widget._run()
    assert len(viewer.layers) == num_layers + 1

    # test overlap value validation
    widget.overlap_dsb.setValue(0.5)
    widget._initialize_tiler()
    assert widget.overlap_dsb.value() == 0.5

    widget.overlap_dsb.setValue(2)
    widget._initialize_tiler()
    assert widget.overlap_dsb.value() == 2

    widget.overlap_dsb.setValue(2.1)
    widget._initialize_tiler()
    assert widget.overlap_dsb.value() == 2


# TODO migrate this test functino with the above?
def test_generate_preview(make_napari_viewer, napari_plugin_manager):
    napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
    viewer = make_napari_viewer()
    _, widget = viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name="Tiler Widget"
    )
    viewer.add_image(np.random.random((512, 512)))
    num_layers = len(viewer.layers)
    widget.preview_chkb.setChecked(True)
    assert len(viewer.layers) == num_layers + 1

    widget._generate_preview_layer()
    assert len(viewer.layers) == num_layers + 1

    widget.preview_chkb.setChecked(False)
    assert len(viewer.layers) == num_layers


@pytest.mark.parametrize(
    "image_data,rgb",
    [
        (np.random.random((512, 512)), False),
        (np.random.random((5, 512, 512)), False),
        (np.random.random((512, 512, 3)), True),
    ],
)
def test_merger_widget(
    image_data, rgb, make_napari_viewer, napari_plugin_manager
):
    napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
    viewer = make_napari_viewer()
    _, tiler_widget = viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name="Tiler Widget"
    )
    _, merger_widget = viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name="Merger Widget"
    )
    viewer.add_image(image_data, rgb=rgb)

    # test run
    num_layers = len(viewer.layers)
    tiler_widget._run()

    merger_widget.image_select.native.setCurrentIndex(1)
    num_layers = len(viewer.layers)
    merger_widget._run()
    assert len(viewer.layers) == num_layers + 1
