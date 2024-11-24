# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from nanocube.context.context import Context

if TYPE_CHECKING:
    from nanocube.cube import Cube
    from nanocube.schema import Measure
    from nanocube.schema import Dimension


class DimensionContext(Context):
    """
    A context representing a dimension of the cube.
    """

    def __init__(self, cube: Cube, parent: Context | None, address: Any = None, row_mask: np.ndarray | None = None,
                 measure: Measure | None = None, dimension: Dimension | None = None, resolve: bool = True):
        super().__init__(cube=cube, address=address, parent=parent, row_mask=row_mask,
                         measure=measure, dimension=dimension, resolve=resolve)

        if cube.settings.populate_members:
            # Support for dynamic attributes
            for member in dimension.members:
                member = member.replace(" ", "_")
                if member not in self.__dict__:
                    from nanocube.context.context_resolver import ContextResolver
                    member_context = ContextResolver.resolve(parent=self, address=member,
                                                             dynamic_attribute=True, target_dimension=dimension)
                    setattr(self, member, member_context)

    @property
    def members(self) -> list:
        return self._dimension.members

    @property
    def count(self) -> int:
        """
        Returns the number of unique members in the dimension matching the current context.
        """
        if self._row_mask is not None:
            records = self._df.iloc[self._row_mask][self._dimension.column].nunique()
            return records
        else:
            return self._df[self._dimension.column].nunique()

    @property
    def unique(self) -> list:
        """
        Returns a list of unique members in the dimension matching the current context.
        """
        if self._row_mask is not None:
            return self._df.iloc[self._row_mask][self._dimension.column].unique().tolist()
        else:
            return self._df[self._dimension.column].unique().tolist()

    def __len__(self):
        return self.count
