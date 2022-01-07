"""Contains the DimensionsInput container widget."""

from typing import List, Optional, Tuple

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


class DimensionsInput(QWidget):
    """A container for tile dimensions input."""

    valueChanged = Signal()

    # dims to determine max dims available for image
    def __init__(
        self,
        data_shape: Optional[Tuple[int]] = None,
        axis_labels: Optional[str] = None,
    ) -> None:
        """Init DimensionsInput.

        Args:
            data_shape (Optional[ArrayLike], optional): [description]. Defaults to None.
            axis_labels (Optional[str], optional): [description]. Defaults to None.
        """
        super().__init__()

        # FIXME does not recognize difference between XY(Z) and XY(RGB)
        self.data_shape = data_shape  # type: ignore
        if axis_labels is not None:
            self.axis_labels = axis_labels

        # construct layout
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        xy_dims_field = self.DimensionField(
            2, [128, 128], ["X", "Y"], add_btn=True, del_btn=False
        )
        xy_dims_field.valueChanged.connect(self.valueChanged)
        self.layout().addWidget(xy_dims_field)

    @property
    def dims(self) -> np.ndarray:
        """Return an array in the order of input fields."""
        dims = np.array([], dtype=int)
        for i in range(self.layout().count()):
            field = self.layout().itemAt(i)
            dims = np.append(dims, field.widget().dims)
        return np.array(dims).flatten()

    @property
    def data_shape(self) -> Tuple[int]:
        return self._data_shape

    @data_shape.setter
    def data_shape(self, value) -> None:
        self._data_shape = value

    @property
    def _max_ndims(self) -> int:
        # napari will send ndim = 2 for 2D RGB, but shape will be length 3...
        return len(self.data_shape)

    def _add_below(self, idx) -> None:
        extra_dim = self.DimensionField()
        extra_dim.valueChanged.connect(self.valueChanged)
        self.layout().insertWidget(idx + 1, extra_dim)
        num_fields = len(self.dims)
        if num_fields > self._max_ndims:
            raise ValueError("Warning: too many dimensions for selected layer.")

    class DimensionField(QWidget):
        """Class for dimension input fields."""

        valueChanged = Signal()

        def __init__(
            self,
            num_fields: int = 1,
            values: Optional[List[int]] = None,
            labels: Optional[List[str]] = None,
            separator: str = "×",
            add_btn: bool = True,
            del_btn: bool = True,
        ) -> None:
            """Init DimensionField class."""
            super().__init__()
            # validate args
            if values is not None and len(values) != num_fields:
                raise ValueError(
                    "Number of values must match number of fields. Input "
                    f"{len(values)} values and {num_fields} fields."
                )
            if labels is not None and len(labels) != num_fields:
                raise ValueError(
                    "Number of labels must match number of fields. Input "
                    f"{len(labels)} labels and {num_fields} fields."
                )
            # set defaults
            if values is None:
                values = [128] * num_fields
            # construct the layout
            self.setLayout(QHBoxLayout())
            self.layout().setContentsMargins(0, 0, 0, 0)
            # number of values matches number of fields
            self._fields: List[QSpinBox] = []
            for val in values:
                self.layout().addWidget(QLabel(separator))
                sb = QSpinBox(minimum=0, maximum=10000)
                sb.setValue(val)
                sb.valueChanged.connect(self.valueChanged)
                self._fields.append(sb)
                self.layout().addWidget(sb)
            if del_btn:
                self._del_btn = QPushButton("⊖")
                self._del_btn.clicked.connect(self._remove)
                self.layout().addWidget(self._del_btn)
            if add_btn:
                self._add_btn = QPushButton("⊕")
                self._add_btn.clicked.connect(self._add_below)
                self.layout().addWidget(self._add_btn)

        def _add_below(self) -> None:
            idx = self.parent().layout().indexOf(self)
            self.parent()._add_below(idx)

        def _remove(self) -> None:
            """Remove self from layout and delete."""
            self.setParent(None)
            del self

        @property
        def dims(self) -> np.ndarray:
            """Return dimension(s) from input field(s)."""
            return np.array(
                [field.value() for field in self._fields],
                dtype=int,
            )
