# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from nanocube.context.context import Context

if TYPE_CHECKING:
    from nanocube.cube import Cube
    from nanocube.schema import Measure
    from nanocube.schema import Dimension
    from nanocube.schema import MemberSet


class MemberContext(Context):
    """
    A context representing a member or set of members of the cube.
    """

    # todo: implement something like: cdf.products[cdf.sales > 100]
    def __init__(self, cube: Cube, parent: Context | None, address: Any = None, row_mask: np.ndarray | None = None,
                 measure: Measure | None = None, dimension: Dimension | None = None,
                 members: MemberSet | None = None, member_mask: np.ndarray | None = None, resolve: bool = True):
        super().__init__(cube=cube, address=address, parent=parent, row_mask=row_mask,
                         measure=measure, dimension=dimension, resolve=resolve)
        self._members: MemberSet = members
        self._member_mask = member_mask

    @property
    def members(self) -> 'MemberSet':
        return self._members
