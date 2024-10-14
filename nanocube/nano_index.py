# nanocube - Copyright (c)2024, Thomas Zeutschler, MIT license
from abc import abstractmethod
from array import array
from enum import Enum
from functools import reduce

import numpy as np
import pandas as pd
import sortednp as snp
from pyroaring import BitMap


class IndexingMethod(Enum):
    roaring = "roaring"
    numpy = "numpy"

    @staticmethod
    def from_str(label):
        if isinstance(label, str):
            return IndexingMethod.numpy if label.lower().strip() == "numpy" else IndexingMethod.roaring
        return label

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return self.value == other.value

class NanoIndex:
    @abstractmethod
    def get_rows(self, **kwargs) -> array | bool:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> dict:
        pass

    @staticmethod
    def create(df: pd.DataFrame, dimensions: 'list | None' = None,
               indexing_method: IndexingMethod | str = IndexingMethod.roaring):
        if isinstance(indexing_method, str):
            indexing_method = IndexingMethod.from_str(indexing_method)
        if indexing_method == IndexingMethod.roaring:
            return NanoRoaringIndex(df, dimensions)
        elif indexing_method == IndexingMethod.numpy:
            return NanoNumpyIndex(df, dimensions)


class NanoRoaringIndex(NanoIndex):
    """NanoCube index."""

    def __init__(self, df: pd.DataFrame, dimensions: 'list | None' = None):
        self._dimensions: dict = dict([(col, i) for i, col in enumerate(dimensions)])
        self._bitmaps: list = []  # bitmaps per dimension per member containing the row ids of the DataFrame
        for dimension in self.dimensions.keys():
            member_bitmaps = {}
            for row, member in enumerate(df[dimension].to_list()):
                if member not in member_bitmaps:
                    member_bitmaps[member] = BitMap([row])
                else:
                    member_bitmaps[member].add(row)
            self._bitmaps.append(member_bitmaps)

    @property
    def dimensions(self) -> dict:
        return self._dimensions

    def get_rows(self, **kwargs) -> array | bool:
        if kwargs:
            bitmaps = [(reduce(lambda x, y: x | y, [self._bitmaps[d][m] for m in kwargs[dim]])
                        if (isinstance(kwargs[dim], list) or isinstance(kwargs[dim], tuple)) and not isinstance(
                kwargs[dim], str)
                        else self._bitmaps[d][kwargs[dim]]) for d, dim in enumerate(self.dimensions.keys()) if
                       dim in kwargs]
            if bitmaps:
                bitmaps = sorted(bitmaps, key=lambda l: len(l))
                return reduce(lambda x, y: x & y, bitmaps).to_array() if bitmaps else False
            else:
                return False
        else:
            return True


class NanoNumpyIndex(NanoIndex):
    """NanoCube index."""

    def __init__(self, df: pd.DataFrame, dimensions: 'list | None' = None):
        self._dimensions: dict = dict([(col, i) for i, col in enumerate(dimensions)])
        self._bitmaps: list = []  # bitmaps per dimension per member containing the row ids of the DataFrame
        for col in self.dimensions.keys():
            member_bitmaps = {}
            for row, member in enumerate(df[col].to_list()):
                if member not in member_bitmaps:
                    member_bitmaps[member] = BitMap([row])
                else:
                    member_bitmaps[member].add(row)

            for v in member_bitmaps.keys():
                member_bitmaps[v] = np.array(member_bitmaps[v].to_array())
            self._bitmaps.append(member_bitmaps)

    @property
    def dimensions(self) -> dict:
        return self._dimensions

    def get_rows(self, **kwargs) -> array | bool:
        if kwargs:

            bitmaps = [(reduce(lambda x, y: snp.merge(x, y, duplicates=snp.MergeDuplicates.DROP), [self._bitmaps[d][m] for m in kwargs[dim]])
                        if isinstance(kwargs[dim], list | tuple) and not isinstance(kwargs[dim], str)
                        else self._bitmaps[d][kwargs[dim]]) for d, dim in enumerate(self.dimensions.keys()) if dim in kwargs]

            if bitmaps:
                bitmaps = sorted(bitmaps, key=lambda l: len(l))
                return reduce(lambda x, y: snp.intersect(x, y, duplicates=snp.IntersectDuplicates.DROP),
                              bitmaps) if bitmaps else False
            else:
                return False
        else:
            return True
