# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

import numpy as np
import pandas as pd


class Measure:
    """
    Represents a measure within a Cube. Each measure is mapped to a column in the underlying Pandas dataframe.
    """

    # todo: add support for aliases
    def __init__(self, df: pd.DataFrame, column, alias: str | None = None, number_format: str | None = None):
        self._df: pd.DataFrame = df

        self._column = column
        self._alias: str | None = alias
        self._column_ordinal = df.columns.get_loc(column)
        self._dtype = df[column].dtype
        self._values: np.ndarray | None = None
        self._number_format: str | None = number_format

    @property
    def column(self):
        """
        Returns the column name in underlying Pandas dataframe the measure refers to.
        """
        return self._column

    @property
    def df(self) -> pd.DataFrame:
        """
        Returns the underlying Pandas dataframe of the cube.
        """
        return self._df

    @property
    def alias(self) -> str:
        """
        Returns the alias of the measure if defined, `None`otherwise.
        """
        return self._alias

    @property
    def number_format(self) -> str | None:
        """
        Returns the number format of the measure.
        """
        return self._number_format

    def to_dict(self):
        d = {'column': self._column}
        if self._alias:
            d['alias'] = self._alias
        if self._number_format:
            d['number_format'] = self._number_format
        return d

    def __len__(self):
        return len(self._df)

    def __str__(self):
        return self._column

    def __repr__(self):
        return self._column

    @property
    def min(self) -> int | float:
        return self._df[self._column].min()

    @property
    def max(self) -> int | float:
        return self._df[self._column].max()

    @property
    def sum(self) -> int | float:
        return self._df[self._column].sum()

    @property
    def mean(self) -> float:
        return self._df[self._column].mean()

    @property
    def median(self) -> float:
        return self._df[self._column].median()

    @property
    def std(self) -> float:
        return self._df[self._column].std()

    @property
    def var(self) -> float:
        return self._df[self._column].var()

    @property
    def count(self) -> int:
        return self._df[self._column].count()

    @property
    def unique(self) -> list[int | float]:
        return self._df[self._column].unique().tolist()

    def __min__(self):
        return self._df[self._column].min()

    def __max__(self):
        return self._df[self._column].max()

    def __sum__(self):
        return self._df[self._column].sum()

    def __mean__(self):
        return self._df[self._column].mean()

    def __median__(self):
        return self._df[self._column].median()

    def __std__(self):
        return self._df[self._column].std()

    def __var__(self):
        return self._df[self._column].var()

    def __count__(self):
        return self._df[self._column].count()

    def __unique__(self):
        return self._df[self._column].unique()
