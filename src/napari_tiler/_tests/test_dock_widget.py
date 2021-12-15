import napari_tiler
import pytest

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


@pytest.mark.parametrize("image_name", ["cells3d", "astronaut"])
def test_tiler_widget_3d(image_name, make_napari_viewer, napari_plugin_manager):
    napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
    viewer = make_napari_viewer()
    _, widget = viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name="Tiler Widget"
    )
    viewer.open_sample("scikit-image", image_name)
    num_layers = len(viewer.layers)
    widget._run()
    assert len(viewer.layers) == num_layers + 1


# def test_generate_preview(make_napari_viewer, napari_plugin_manager):
#     napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
#     viewer = make_napari_viewer()
#     widget = viewer.window.add_plugin_dock_widget(
#         plugin_name=MY_PLUGIN_NAME, widget_name="Tiler Widget"
#     )[-1]
#     image = viewer.open_sample("scikit-image", "astronaut")


# def test_tiler_widget_rgb(make_napari_viewer, napari_plugin_manager):
#     napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
#     viewer = make_napari_viewer()
#     viewer.window.add_plugin_dock_widget(
#         plugin_name=MY_PLUGIN_NAME, widget_name="make_tiles"
#     )
#     # RGB example


# def test_merger_widget():
#     pass
