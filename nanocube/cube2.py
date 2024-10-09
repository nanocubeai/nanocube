from functools import reduce

import numpy as np
import pandas as pd
from pandas.core.dtypes.common import is_numeric_dtype, is_bool_dtype, is_float_dtype
import sortednp as snp
from pyroaring import BitMap


def start_stop_arr(a):
    mask = np.concatenate(([True], a[1:] != a[:-1], [True]))
    idx = np.flatnonzero(mask)
    idx2 = np.concatenate((idx[:-1,None], (idx[1:,None]-1)),axis=1)
    return idx2


class Cube2:
    def __init__(self, df: pd.DataFrame, measures = None, dimensions = None, caching=False):
        # self.df = df.reset_index(drop=True)
        self.df = df
        self.index = {}

        self.measures = [c for c in df.columns if is_numeric_dtype(df[c].dtype) and not is_bool_dtype(df[c].dtype)] if measures is None else measures
        self.dimensions = [c for c in df.columns if not c in self.measures and not is_float_dtype(df[c].dtype)] if dimensions is None else dimensions

        self.compute_index()

    def compute_index(self):
        self.index = {}

        for col in self.dimensions:
            col_index = {}

            for i, val in enumerate(self.df[col].values):
                if val not in col_index:
                    col_index[val] = BitMap([i])
                else:
                    col_index[val].add(i)

            for val in col_index:
                col_index[val] = np.array(col_index[val].to_array())

            self.index[col] = col_index

    def get(self, *args, **kwargs):
        matches = []

        for col, value_or_values in kwargs.items():
            col_index = self.index[col]

            if isinstance(value_or_values, list):
                multi_index = []
                for v in value_or_values:
                    multi_index.append(col_index[v])
                col_matches_index = reduce(lambda x, y: snp.merge(x, y, duplicates=snp.MergeDuplicates.DROP), multi_index)
            else:
                col_matches_index = col_index[value_or_values]

            matches.append(col_matches_index)

        matches_sorted = sorted(matches, key=lambda l: len(l))

        matches = reduce(lambda x, y: snp.intersect(x, y, duplicates=snp.IntersectDuplicates.DROP), matches_sorted)

        result = []

        if len(args) > 0:
            result_cols = args
        else:
            result_cols = self.measures

        for col in result_cols:
            result.append(np.nansum(self.df[col].values[matches]).item())

        if len(args) == 1:
            return result[0]
        elif len(args) == 0:
            return dict(zip(result_cols, result))

        return result