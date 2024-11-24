# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from nanocube.context.context import Context

if TYPE_CHECKING:
    from nanocube.cube import Cube
    from nanocube.schema import Dimension


class MemberNotFoundContext(Context):
    """
    A context representing a member that was not found in the cube.
    """

    def __init__(self, cube: Cube, parent: Context | None, address: Any = None,
                 dimension: Dimension | None = None):
        empty_mask = pd.DataFrame(columns=["x"]).index.to_numpy()  # a hack. Can we do better?
        super().__init__(cube=cube, address=address, parent=parent, row_mask=empty_mask,
                         measure=parent.measure, dimension=dimension, resolve=False)

    @property
    def is_valid(self):
        return False
