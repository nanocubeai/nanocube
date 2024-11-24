# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
from __future__ import annotations

from typing import Iterable

from nanocube.schema import Measure


class MeasureCollection(Iterable[Measure]):
    """
    Represents the available/defined Measures of a Cube.
    """

    def __init__(self, parent=None):
        self._measures: dict = {}
        self._counter: int = 0
        self._measure_list: list = []
        self._parent = parent
        self._default_measure = None
        pass

    def __iter__(self) -> MeasureCollection:
        self._counter = 0
        self._measure_list = list(
            set(self._measures.values()))  # unique values needed, duplicates may be caused by aliasing
        return self

    def __next__(self) -> Measure:
        if self._counter >= len(self._measures):
            raise StopIteration
        dim = self._measure_list[self._counter]
        self._counter += 1
        return dim

    def __len__(self):
        return len(self._measures)

    def __getitem__(self, item) -> Measure | None:
        if len(self._measures) == 0:
            return None
        if isinstance(item, str):
            return self._measures[item]
        return self._measure_list[item]

    def __contains__(self, item) -> bool:
        return item in self._measures

    def add(self, measure: Measure):
        self._measures[measure.column] = measure
        if measure.alias is not None:
            self._measures[measure.alias] = measure
        self._measure_list = list(self._measures.values())

    @property
    def default(self) -> Measure:
        """
        Returns:
            Returns the default measure of the Cube. If not defined otherwise by a cube schema
            or manually set by the user, the default measure refers to the first numeric column (int or float)
            in the cube, evaluated from left to right.
        """
        if self._default_measure is None:
            return self[0]
        else:
            return self._default_measure

    @default.setter
    def default(self, value: Measure | str):
        """
        Sets the default measure of the Cube.
        Parameters:
            value:  The name of the measure to be set as default.
        """
        if isinstance(value, Measure):
            value = value.column
        if value not in self:
            raise ValueError(f"Measure '{value}' not found in MeasureCollection.")
        self._default_measure = self[value]
