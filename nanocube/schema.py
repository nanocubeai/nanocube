# nanocube - Copyright (c)2024, Thomas Zeutschler, MIT license
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SchemaDimension:
    """Defines a Dimension of a NanoCube."""
    ordinal: int
    column: str
    dtype: np.dtype | None = None
    description: str = None


@dataclass
class SchemaMeasure:
    """Defines a Measure of a NanoCube."""
    ordinal: int
    column: str
    dtype: np.dtype | None = None
    description: str | None = None
    format: str | None = None


class Schema:
    """
    Schema defining the dimensions and measures of a NanoCube.
    """

    def __init__(self, df: Any | None = None, dimensions: Any | None = None, measures: Any | None = None):
        self.measures: list[SchemaMeasure] = []
        self._load_measures(df, measures)
        self.dimensions: list[SchemaDimension] = []
        self._load_dimensions(df, dimensions)

    def _load_dimensions(self, df, dimensions):

        if isinstance(dimensions, str):
            dimensions = SchemaDimension(ordinal=0, column=dimensions)
        if isinstance(dimensions, SchemaDimension):
            self.dimensions.append(dimensions)
            return
        if not isinstance(dimensions, list | tuple):
            raise ValueError("Argument `dimensions` must be list or tuple of type "
                             "`SchemaDimension` or `str` representing a columns name.")

        for i, dimension in enumerate(dimensions):
            if isinstance(dimension, str):
                self.dimensions.append(SchemaDimension(ordinal=i, column=dimension))
            else:
                self.dimensions.append(dimension)

    def _load_measures(self, df, measures):
        if measures is None:
            return
        if isinstance(measures, str):
            measures = SchemaMeasure(ordinal=0, column=measures)
        if isinstance(measures, SchemaMeasure):
            self.measures.append(measures)
            return
        if not isinstance(measures, list | tuple):
            raise ValueError("Argument `measures` must be list or tuple of type "
                             "`SchemaMeasure` or `str` representing a columns name.")

        for i, measure in enumerate(measures):
            if isinstance(measure, str):
                self.measures.append(SchemaDimension(ordinal=i, column=measure))
            else:
                self.measures.append(measure)
