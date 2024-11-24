# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd

from nanocube.schema import DimensionCollection
from nanocube.schema import MeasureCollection


class Ambiguities:
    """
    Represents a list of ambiguities found within a Cube. Used to check if a cube can be accessed unambiguously without
    using explicit dimension names, e.g. if `cube["Apple", "Online"]` or `cube.Apple.Online` can be used instead
    of `cube["product"="Apple", "channel"="Online"]`.
    Each ambiguity is a situation where one or many dimension members (or measure names) are contained in more than
    one column. To check ambiguities, use the `Ambiguities` property of a `Cube` object as follows:

    ```python
    cdf = cubed(df)
    if cdf.Ambiguities:
        print("Better be cautious, there are ambiguities in the cube.")
    ```
    """

    def __init__(self, df: pd.DataFrame, dimensions: DimensionCollection, measures: MeasureCollection):
        self._ambiguities: list = []
        self._members: set | None = None
        self._find_ambiguities(df, dimensions, measures)

    @property
    def members(self) -> set | None:
        """
        Returns a set of all ambiguous members found in the cube. If no ambiguities are found, `None` is returned.
        """
        if self._members is None:
            self._members = set()
            for amb in self._ambiguities:
                self._members.update(amb['members'])
        return self._members

    def to_list(self) -> list[dict]:
        """
        Returns a list of all ambiguities found in the cube.
        """
        return self._ambiguities

    def is_ambiguous(self, member) -> bool:
        """
        Checks if a member is ambiguous in the cube.
        """
        return member in self.members

    @property
    def any(self) -> bool:
        """
        Returns `True` if any ambiguities are found in the cube, otherwise `False`.
        """
        return len(self._ambiguities) > 0

    def _find_ambiguities(self, df: pd.DataFrame, dimensions: DimensionCollection, measures: MeasureCollection):
        """
        Finds ambiguities between dimensions and measures of the cube.
        """
        dims = dimensions.to_list()
        # find and collect all ambiguities between each 2 dimensions
        for i, dim in enumerate(dims[:-1]):
            for j, other in enumerate(dims[i + 1:]):
                if dim.dtype == other.dtype:  # only compare dimensions of the same type
                    # print(f"checking ambiguities between '{dim.name}'({dim.dtype}) and '{other.name}({other.dtype}):")
                    ambiguous_members = set(dim.members) & set(other.members)  # intersection of 2 sets
                    if ambiguous_members:
                        members = list(ambiguous_members)
                        ambiguity = {
                            "message": f"{len(members)} ambiguit{'y' if len(members) == 1 else 'ies'} between dimensions '{dim.name}' and '{other.name}' found "
                                       f"on member{'' if len(members) == 1 else 's'}: {', '.join(members[:min(3, len(members))])}{'' if len(members) <= 3 else ' ...'}",
                            "dim1": dim.name,
                            "dim2": other.name,
                            "count": len(members),
                            "members": members}
                        self._ambiguities.append(ambiguity)

    # region Overloads
    def __len__(self):
        # todo: decide what to return here, number of ambiguities between dimensions or number of ambiguous members?
        return len(self._ambiguities)

    def __getitem__(self, item):
        return self._ambiguities[item]

    def __iter__(self):
        return iter(self._ambiguities)

    def __str__(self):
        if len(self._ambiguities) == 0:
            return "No ambiguities found."
        return f"Ambiguities:\n" + "\n".join([amb['message'] for amb in self._ambiguities])

    def __bool__(self):
        return len(self._ambiguities) > 0

    def __eq__(self, other):
        if isinstance(other, bool):
            return (len(self._ambiguities) > 0) == other
        if isinstance(other, int):
            return len(self._ambiguities) == other
        return self._ambiguities == other._ambiguities

    def __gt__(self, other):
        return len(self._ambiguities) > other

    def __ge__(self, other):
        return len(self._ambiguities) >= other

    def __lt__(self, other):
        return len(self._ambiguities) < other

    def __le__(self, other):
        return len(self._ambiguities) <= other
    # endregion
