# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from nanocube.context.context import Context

if TYPE_CHECKING:
    from nanocube.cube import Cube
    from nanocube.schema import Measure
    from nanocube.schema import Dimension


class MeasureContext(Context):
    """
    A context representing a measure of the cube.
    """

    def __init__(self, cube: Cube, parent: Context | None = None, address: Any = None, row_mask: np.ndarray | None = None,
                 measure: Measure | None = None, dimension: Dimension | None = None, resolve: bool = True,
                 filtered: bool = False):
        self._filtered: bool = filtered
        super().__init__(cube=cube, address=address, parent=parent, row_mask=row_mask,
                         measure=measure, dimension=dimension, resolve=resolve, filtered=filtered)
