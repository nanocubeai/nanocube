# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
from __future__ import annotations

from typing import Iterable

from nanocube.schema import Dimension


class DimensionCollection(Iterable[Dimension]):
    """
    Represents the available/defined Dimensions of a Cube.
    """

    def __init__(self):
        self._dims: dict = {}
        self._counter: int = 0
        self._dims_list: list = []
        pass

    def __iter__(self) -> DimensionCollection:
        self._counter = 0
        self._dims_list = list(set(self._dims.values()))  # unique values needed, duplicates may be caused by aliasing
        # self._dims_list = list(self._dims.values())
        return self

    def __next__(self) -> Dimension:
        if self._counter >= len(self._dims_list):
            raise StopIteration
        dim = self._dims_list[self._counter]
        self._counter += 1
        return dim

    def __len__(self):
        return len(self._dims)

    def __getitem__(self, item) -> Dimension:
        if isinstance(item, int):
            return list(self._dims.values())[item]
        return self._dims[item]

    def __contains__(self, key):
        return key in self._dims

    def add(self, dimension: Dimension):
        name = dimension.column
        if name in self._dims:
            raise ValueError(f"A dimension '{name}' already exists.")

        self._dims[name] = dimension
        if dimension.alias is not None:
            self._dims[dimension.alias] = dimension


        # For future use...
        # # Add all name variants to the collection "List Price" >>> "list price", "List_Price", "list_price"
        # lcase_name = name.lower()
        # if not lcase_name in self._dims:
        #     self._dims[lcase_name] = dimension
        #
        # underscored_name = name.replace(" ", "_")
        # if not underscored_name in self._dims:
        #     self._dims[underscored_name] = dimension
        #
        # lcase_underscored_name = lcase_name.replace(" ", "_")
        # if not lcase_underscored_name in self._dims:
        #     self._dims[lcase_underscored_name] = dimension



    def to_set(self):
        return set(self._dims.values())

    def to_list(self):
        return list(self._dims.values())

    def excluded(self, exclude: Dimension | None = None):
        if exclude is None:
            return self._dims.values()
        return [dim for dim in self._dims.values() if dim != exclude]

    def starting_with_this_dimension(self, first: Dimension | None = None):
        if first is None:
            return self._dims.values()
        result = [first]
        result.extend([dim for dim in self._dims.values() if dim != first])
        return result
