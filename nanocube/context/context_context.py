# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from nanocube.context.context import Context

if TYPE_CHECKING:
    from nanocube.context.filter_context import FilterContext


class ContextContext(Context):
    """
    A context representing by an existing context
    """

    def __init__(self, parent: Context, nested: Context):
        from nanocube.context.filter_context import FilterContext

        # merge the row masks of the parent and the nested context, e.g. parent[nested]
        # Note: This will be also called if both dimensions are both None.
        #       This happens when both contexts are CubeContexts or derived from CubeContexts.
        if parent.dimension == nested.dimension:
            parent_row_mask = parent._get_row_mask(before_dimension=parent.dimension)
            nested_row_mask = nested._row_mask

            if parent.member_mask is not None and nested.member_mask is not None:
                member_mask = np.union1d(parent.member_mask, nested.member_mask)
            elif parent.member_mask is not None:
                member_mask = parent.member_mask
            else:
                member_mask = nested.member_mask  # can be None

            if parent_row_mask is None:
                if member_mask is not None:
                    row_mask = member_mask
                else:
                    row_mask = nested_row_mask
            else:
                if member_mask is None:
                    row_mask = parent_row_mask
                else:
                    row_mask = np.intersect1d(parent_row_mask, member_mask, assume_unique=True)

        elif isinstance(nested.parent, FilterContext):
            if parent.row_mask is None:
                row_mask = nested.row_mask
            elif nested.row_mask is None:
                row_mask = parent.row_mask
            else:
                row_mask = np.intersect1d(parent.row_mask, nested.row_mask, assume_unique=True)

        else:
            member_mask = nested.member_mask
            if parent.row_mask is None:
                row_mask = nested.row_mask
            else:
                row_mask = np.intersect1d(parent.row_mask, member_mask, assume_unique=True)

        super().__init__(cube=parent.cube, address=nested.address, parent=parent,
                         row_mask=row_mask, member_mask=nested.member_mask,
                         measure=nested.measure, dimension=nested.dimension,
                         resolve=False)
        self._referenced_context = nested

    @property
    def referenced_context(self):
        return self._referenced_context
