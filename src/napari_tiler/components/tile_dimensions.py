"""Contains the TileDimensions container widget."""

from typing import List

import numpy as np
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class TileDimensions(QWidget):
    """A container for tile dimensions input."""

    valueChanged = Signal()

    # dims to determine max dims available for image
    def __init__(self, max_dims: int = 2) -> None:
        """Init the TileDimensions class."""
        super().__init__()

        xy_dims_field = self.XYDimensionField()
        xy_dims_field.valueChanged.connect(self.valueChanged)

        self.max_dims = max_dims
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(xy_dims_field)

    @property
    def max_dims(self) -> int:
        """Return max dimensions."""
        return self._max_dims

    @max_dims.setter
    def max_dims(self, value: int) -> None:
        self._max_dims = value

    def get_dims(self) -> np.ndarray:
        """Return an array in the order of input fields."""
        dims = np.array([], dtype=int)
        layout = self.layout()

        for i in range(layout.count()):
            field = layout.itemAt(i)
            dims = np.append(dims, field.widget().get_dims())
        return np.array(dims).flatten()

    def _add_below(self, idx) -> None:
        extra_dim = self.ExtraDimensionField()
        extra_dim.valueChanged.connect(self.valueChanged)
        self.layout().insertWidget(idx + 1, extra_dim)
        num_fields = len(self.get_dims())
        if num_fields > self.max_dims:
            raise ValueError("Warning: too many dimensions entered.")

    class DimensionField(QWidget):
        """Base class for dimension input fields.

        Class depends on parent having ``_add_below`` method for creating
        extra dimension widgets.
        """

        valueChanged = Signal()

        def __init__(self) -> None:
            """Init DimensionField class."""
            super().__init__()
            self.setLayout(QHBoxLayout())
            self.layout().setContentsMargins(0, 0, 0, 0)

            self._del_btn = QPushButton("⊖")
            self._del_btn.clicked.connect(self._remove)
            self._add_btn = QPushButton("⊕")
            self._add_btn.clicked.connect(self._add_below)

        def get_dims(self) -> np.ndarray:
            """Return dimension(s) from input field(s)."""
            return np.array(
                [field.value() for field in self._get_fields()], dtype=int
            )

        def _remove(self) -> None:
            """Remove self from layout and delete."""
            self.setParent(None)
            del self

        def _add_below(self) -> None:
            idx = self.parent().layout().indexOf(self)
            self.parent()._add_below(idx)

        def _get_fields(self) -> List:
            return [
                field
                for field in self._iterate_layout_widgets()
                if isinstance(field, QSpinBox)
            ]

        def _iterate_layout_widgets(self) -> QWidget:
            layout = self.layout()
            for i in range(layout.count()):
                yield layout.itemAt(i).widget()

    class XYDimensionField(DimensionField):
        """Dimension input for X and Y sizes."""

        def __init__(self) -> None:
            """Init XYDimensionField class."""
            super().__init__()
            self._x_dim_sb = QSpinBox(minimum=0, maximum=10000)
            self._x_dim_sb.setValue(128)
            self._x_dim_sb.valueChanged.connect(self.valueChanged)
            self._y_dim_sb = QSpinBox(minimum=0, maximum=10000)
            self._y_dim_sb.setValue(128)
            self._y_dim_sb.valueChanged.connect(self.valueChanged)

            self.layout().addWidget(self._x_dim_sb)
            self.layout().addWidget(QLabel("×"))
            self.layout().addWidget(self._y_dim_sb)
            self.layout().addWidget(self._add_btn)

    class ExtraDimensionField(DimensionField):
        """Dimension input for an extra dimension (e.g. Z, T, ...)."""

        def __init__(self) -> None:
            """Init ExtraDimensionField class."""
            super().__init__()

            self._dim_sb = QSpinBox(minimum=0, maximum=10000)
            self._dim_sb.setValue(5)
            self._dim_sb.valueChanged.connect(self.valueChanged)

            layout = self.layout()
            layout.addWidget(QLabel("×"))
            layout.addWidget(self._dim_sb)
            layout.addWidget(self._del_btn)
            layout.addWidget(self._add_btn)
