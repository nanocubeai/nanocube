# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from nanocube.context.context import Context
from nanocube.context.enums import BooleanOperation

if TYPE_CHECKING:
    pass

class BooleanOperationContext(Context):
    """ A context representing a boolean operation between two Context objects."""

    def __init__(self, left: Context, right: Context | None = None,
                 operation: BooleanOperation = BooleanOperation.AND):
        self._left: Context = left
        self._right: Context | None = right
        self._operation: BooleanOperation = operation
        match self._operation:
            case BooleanOperation.AND:
                row_mask = np.intersect1d(left.row_mask, right.row_mask, assume_unique=True)
            case BooleanOperation.OR:
                row_mask = np.union1d(left.row_mask, right.row_mask)
            case BooleanOperation.XOR:
                row_mask = np.setxor1d(left.row_mask, right.row_mask, assume_unique=True)
            case BooleanOperation.NOT:
                row_mask = np.setdiff1d(left._df.index.to_numpy(), left.row_mask, assume_unique=True)
            case _:
                raise ValueError(f"Invalid boolean operation '{operation}'. Only 'AND', 'OR' and 'XOR' are supported.")

        if self._operation == BooleanOperation.NOT:
            # unary operation
            super().__init__(cube=left.cube, address=None, parent=left.parent,
                             row_mask=row_mask, member_mask=None,
                             measure=left.measure, dimension=left.dimension, resolve=False)
        else:
            # binary operations
            super().__init__(cube=right.cube, address=None, parent=left.parent,
                             row_mask=row_mask, member_mask=None,
                             measure=right.measure, dimension=right.dimension, resolve=False)

    @property
    def left(self) -> Context:
        return self._left

    @property
    def right(self) -> Context | None:
        return self._right

    @property
    def operation(self) -> BooleanOperation:
        return self._operation
