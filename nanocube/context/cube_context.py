# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

from typing import TYPE_CHECKING

from nanocube.context.context import Context

if TYPE_CHECKING:
    from nanocube.cube import Cube


class CubeContext(Context):
    """
    A context representing the cube itself.
    """

    def __init__(self, cube: 'Cube', dynamic_attribute: bool = False):
        super().__init__(cube=cube, address=None, parent=None, row_mask=None, measure=None,
                         dynamic_attribute=dynamic_attribute)
        self._measure = cube.schema.measures.default

        if cube.settings.populate_members:
            # Support for dynamic attributes
            for measure in cube.schema.measures:
                measure_name = measure.column.replace(" ", "_")
                if measure_name not in self.__dict__:
                    from nanocube.context.context_resolver import ContextResolver
                    context = ContextResolver.resolve(parent=self, address=measure_name,
                                                             dynamic_attribute=True)
                    setattr(self, measure_name, context)

            for dimension in cube.dimensions:
                dim_name = dimension.column.replace(" ", "_")
                if dim_name not in self.__dict__:
                    from nanocube.context.context_resolver import ContextResolver
                    context = ContextResolver.resolve(parent=self, address=dim_name,
                                                             dynamic_attribute=True)
                    setattr(self, dim_name, context)

