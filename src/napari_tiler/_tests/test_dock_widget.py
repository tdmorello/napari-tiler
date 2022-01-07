import numpy as np
import pytest

import napari_tiler

# this is your plugin name declared in your napari.plugins entry point
MY_PLUGIN_NAME = "napari-tiler"
# the name of your widget(s)
MY_WIDGET_NAMES = ["Tiler Widget", "Merger Widget"]


sample_layer_data = [
    (np.random.random((512, 512)), False, "image"),  # 2d
    (np.random.random((5, 512, 512)), False, "image"),  # 3d
    (np.random.random((512, 512, 3)), True, "image"),  # rgb
    (np.random.random((512, 512, 4)), True, "image"),  # rgba
    [np.random.randint(0, 100, (512, 512), dtype=int), False, "labels"],
]

sample_layer_ids = ["2d", "3d", "rgb", "rgba", "labels"]


@pytest.mark.parametrize("widget_name", MY_WIDGET_NAMES)
def test_load_widgets(widget_name, make_napari_viewer, napari_plugin_manager):
    """Test that napari loads the widget through the plugin manager."""
    napari_plugin_manager.register(napari_tiler, name=MY_PLUGIN_NAME)
    viewer = make_napari_viewer()
    num_dw = len(viewer.window._dock_widgets)
    viewer.window.add_plugin_dock_widget(
        plugin_name=MY_PLUGIN_NAME, widget_name=widget_name
    )
    assert len(viewer.window._dock_widgets) == num_dw + 1


def test_widgets_no_input(make_napari_viewer):
    """Test error raised when no layer is loaded."""
    viewer = make_napari_viewer()
    tiler_widget = napari_tiler.tiler_widget.TilerWidget(viewer)
    merger_widget = napari_tiler.merger_widget.MergerWidget(viewer)
    viewer.window.add_dock_widget(tiler_widget)
    viewer.window.add_dock_widget(merger_widget)
    with pytest.raises(ValueError):
        tiler_widget._run()
    with pytest.raises(ValueError):
        merger_widget._run()


@pytest.mark.parametrize(
    "layer_data,rgb,layer_type", sample_layer_data, ids=sample_layer_ids
)
def test_tiler_widget_default_parameters(
    make_napari_viewer, layer_data, rgb, layer_type
):
    """Test basic functionality of the tiler widget."""
    viewer = make_napari_viewer()
    widget = napari_tiler.tiler_widget.TilerWidget(viewer)
    viewer.window.add_dock_widget(widget)

    viewer._add_layer_from_data(layer_data, {"rgb": rgb} if rgb else {}, layer_type)
    num_layers = len(viewer.layers)
    widget._run()
    assert len(viewer.layers) == num_layers + 1


@pytest.mark.parametrize(
    "layer_data,rgb,layer_type", sample_layer_data, ids=sample_layer_ids
)
def test_tiler_widget_generate_preview(make_napari_viewer, layer_data, rgb, layer_type):
    """Test basic functionality of the tiler widget."""
    viewer = make_napari_viewer()
    widget = napari_tiler.tiler_widget.TilerWidget(viewer)
    viewer.window.add_dock_widget(widget)

    viewer._add_layer_from_data(layer_data, {"rgb": rgb} if rgb else {}, layer_type)
    num_layers = len(viewer.layers)

    widget.preview_chkb.setChecked(True)
    assert len(viewer.layers) == num_layers + 1
    assert "tiler preview" in viewer.layers

    # test changing parameters updates preview
    old_preview_layer = viewer.layers["tiler preview"].data
    widget.overlap_dsb.setValue(widget.overlap_dsb.value() + 1)
    new_preview_layer = viewer.layers["tiler preview"].data
    assert not np.array_equal(old_preview_layer, new_preview_layer)

    widget.preview_chkb.setChecked(False)
    assert len(viewer.layers) == num_layers
    assert "tiler preview" not in viewer.layers


def test_tiler_widget_show_hide_constant_input(make_napari_viewer):
    """Test that constant QSpinBox hides when mode is not 'constant'."""
    viewer = make_napari_viewer()
    widget = napari_tiler.tiler_widget.TilerWidget(viewer)
    viewer.window.add_dock_widget(widget)

    # FIXME this test is broken, isVisible always returns False
    widget.mode_select.setCurrentIndex(1)
    assert not widget.constant_dsb.isVisible()
    assert not widget.constant_lbl.isVisible()


def test_tiler_widget_parameter_input_validation(make_napari_viewer):
    """Test that user input types are corrected to fit Tiler class."""
    viewer = make_napari_viewer()
    widget = napari_tiler.tiler_widget.TilerWidget(viewer)
    viewer.window.add_dock_widget(widget)
    viewer.add_image(np.random.random((512, 512)))

    widget.overlap_dsb.setValue(0.5)
    widget._initialize_tiler()
    assert widget.overlap_dsb.value() == 0.5

    widget.overlap_dsb.setValue(2)
    widget._initialize_tiler()
    assert widget.overlap_dsb.value() == 2

    widget.overlap_dsb.setValue(2.1)
    widget._initialize_tiler()
    assert widget.overlap_dsb.value() == 2


def test_tiler_widget_add_remove_tile_dimensions(make_napari_viewer):
    """Test that extra tile dimensions can be added and removed."""
    viewer = make_napari_viewer()
    widget = napari_tiler.tiler_widget.TilerWidget(viewer)
    viewer.window.add_dock_widget(widget)
    viewer.add_image(np.random.random((5, 5, 5, 5)))

    dims_layout = widget.tile_dims_container.layout()
    cnt = dims_layout.count()
    dims_layout.itemAt(0).widget()._add_below()
    assert dims_layout.count() == cnt + 1
    dims_layout.itemAt(1).widget()._remove()
    assert dims_layout.count() == cnt


def test_tiler_widget_too_many_dimensions(make_napari_viewer):
    """Tiler widget raises an error when too many tile dimensions."""
    viewer = make_napari_viewer()
    widget = napari_tiler.tiler_widget.TilerWidget(viewer)
    viewer.window.add_dock_widget(widget)
    viewer.add_image(np.random.random((512, 512)))

    # test raises value error when tile dims > image dims
    with pytest.raises(ValueError):
        dims_layout = widget.tile_dims_container.layout()
        dims_layout.itemAt(0).widget()._add_below()


@pytest.mark.parametrize(
    "layer_data,rgb,layer_type", sample_layer_data, ids=sample_layer_ids
)
def test_merger_widget_default_parameters(
    layer_data, rgb, layer_type, make_napari_viewer
):
    """Test that merger widget output matches pre-tiled image."""
    viewer = make_napari_viewer()
    tiler_widget = napari_tiler.tiler_widget.TilerWidget(viewer)
    merger_widget = napari_tiler.merger_widget.MergerWidget(viewer)
    viewer.window.add_dock_widget(tiler_widget)
    viewer.window.add_dock_widget(merger_widget)

    viewer._add_layer_from_data(layer_data, {"rgb": rgb} if rgb else {}, layer_type)
    tiler_widget._run()
    merger_widget.layer_select.native.setCurrentIndex(1)

    # merger creates a new layer
    num_layers = len(viewer.layers)
    merger_widget._run()
    assert len(viewer.layers) == num_layers + 1

    # merged layer is same as original
    merged_image_data = viewer.layers[-1].data
    np.testing.assert_almost_equal(layer_data, merged_image_data)


def test_merger_widget_no_metadata(make_napari_viewer):
    """Merger widget raises error when metadata is not available."""
    viewer = make_napari_viewer()
    merger_widget = napari_tiler.merger_widget.MergerWidget(viewer)
    viewer.window.add_dock_widget(merger_widget)
    viewer.add_image(np.random.random((512, 512)))
    with pytest.raises(ValueError):
        merger_widget._run()
