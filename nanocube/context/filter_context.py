# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from nanocube.context.context import Context

if TYPE_CHECKING:
    from nanocube.schema import Measure
    from nanocube.schema import Dimension

    from nanocube.context.context import MeasureContext


class FilterContext(Context):
    """
    A context representing a filter on another context.
    """

    def __init__(self, parent: Context | None, filter_expression: Any = None, row_mask: np.ndarray | None = None,
                 measure: Measure | None = None, dimension: Dimension | None = None,
                 resolve: bool = True, is_comparison: bool = True):
        self._expression = filter_expression
        self._is_comparison: bool = is_comparison

        if row_mask is None:
            row_mask = parent.row_mask
        super().__init__(cube=parent.cube, address=filter_expression, parent=parent, row_mask=row_mask,
                         measure=parent.measure, dimension=parent.dimension, resolve=resolve)

    def _compare(self, operator: str, other) -> 'MeasureContext':
        from nanocube.context.context import Context
        from nanocube.context.measure_context import MeasureContext

        if isinstance(other, Context):
            other = other.value
        try:
            match operator:
                case "<":
                    row_mask = self._df[self._df[self.measure.column] < other].index.to_numpy()
                case "<=":
                    row_mask = self._df[self._df[self.measure.column] <= other].index.to_numpy()
                case ">":
                    row_mask = self._df[self._df[self.measure.column] > other].index.to_numpy()
                case ">=":
                    row_mask = self._df[self._df[self.measure.column] >= other].index.to_numpy()
                case "==":
                    row_mask = self._df[self._df[self.measure.column] == other].index.to_numpy()
                case "!=":
                    row_mask = self._df[self._df[self.measure.column] != other].index.to_numpy()
                case _:
                    raise ValueError(f"Unsupported comparison '{operator}'.")
        except TypeError as err:
            raise ValueError(f"Unsupported comparison '{operator}' of a Context with "
                             f"an object of type '{type(other)}' and value '{other}' .")

        if self._row_mask is not None:
            row_mask = np.intersect1d(self._row_mask, row_mask, assume_unique=True)
        self._expression = f"{self.measure} {operator} {other}"
        self._address = self._expression
        self._row_mask = row_mask
        return MeasureContext(cube=self.cube, address=self._expression, parent=self, row_mask=row_mask,
                              measure=self.measure, dimension=self.dimension, resolve=False, filtered=False)

    @property
    def expression(self) -> Any:
        return self._expression

    def __lt__(self, other) -> MeasureContext:  # < (less than) operator
        if self._is_comparison:
            return self._compare("<", other)
        else:
            return self.numeric_value < other

    def __gt__(self, other) -> MeasureContext:  # > (greater than) operator
        if self._is_comparison:
            return self._compare(">", other)
        else:
            return self.numeric_value > other

    def __le__(self, other) -> MeasureContext:  # <= (less than or equal to) operator
        if self._is_comparison:
            return self._compare("<=", other)
        else:
            return self.numeric_value <= other

    def __ge__(self, other) -> MeasureContext:  # >= (greater than or equal to) operator
        if self._is_comparison:
            return self._compare(">=", other)
        else:
            return self.numeric_value >= other

    def __eq__(self, other) -> MeasureContext:  # == (equal to) operator
        if self._is_comparison:
            return self._compare("==", other)
        else:
            return self.numeric_value == other

    def __ne__(self, other) -> MeasureContext:  # != (not equal to) operator
        if self._is_comparison:
            return self._compare("!=", other)
        else:
            return self.numeric_value != other
