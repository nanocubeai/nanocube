from functools import reduce

import numpy as np
import pandas as pd
from pandas.core.dtypes.common import is_numeric_dtype, is_bool_dtype, is_float_dtype
import sortednp as snp
from pyroaring import BitMap


class Cube2:
    """
    A super minimalistic (27 lines of code) in-memory OLAP cube implementation for lightning fast point queries
    upon Pandas DataFrames (100x to 1000x times faster than Pandas). By default, all non-numeric columns will be
    used as dimensions and all numeric columns as measures. Roaring Bitmaps (https://roaringbitmap.org) are used
    to construct and query a multi-dimensional cube, Numpy is used for aggregations.
    """
    def __init__(self, df: pd.DataFrame, dimensions: 'list | None' = None, measures:'list | None' = None, caching: bool = True):
        """
        Initialize an in-memory OLAP cube for fast point queries upon a Pandas DataFrame.
        By default, all non-numeric columns will be used as dimensions and all numeric columns as measures if
        not specified otherwise. All column names need to be Python-keyword-compliant. Roaring Bitmaps
        (https://roaringbitmap.org) are used to store and query records, Numpy is used for aggregations.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to be converted to a Cube.
        dimensions : list | None
            (optional) List of column names from the Pandas DataFrame to be used as dimensions.
        measures : list | None
            (optional) List of columns names from the Pandas DataFrame to be used as measures.
        caching : bool
            (optional) If True, the results of the queries will be cached for faster repetitive access.
        Examples
        --------
        >>> import pandas as pd
        >>> from nanocube import NanoCube
        >>> # Create a DataFrame
        >>> df = pd.DataFrame({'customer': [ 'A',  'B',  'A',  'B',  'A'],
        >>>                    'product':  ['P1', 'P2', 'P3', 'P1', 'P2'],
        >>>                    'promo':    [True, False, True, True, False],
        >>>                    'sales':    [ 100,  200,  300,  400,  500],
        >>>                    'cost':     [  60,   90,  120,  200,  240]})
        >>> # Convert to a Cube
        >>> cube = NanoCube(df)
        >>> print(cube.get(customer='A', product='P1'))  # [100, 60]
        >>> print(cube.get(customer='A'))                # [900, 420]
        >>> print(cube.get(promo=True))                  # [800, 380]
        >>> print(cube.get(promo=True))                  # [800, 380]
        """
        measures = [c for c in df.columns if is_numeric_dtype(df[c].dtype) and not is_bool_dtype(df[c].dtype)] if measures is None else measures
        dimensions = [c for c in df.columns if not c in measures and not is_float_dtype(df[c].dtype)] if dimensions is None else dimensions
        self.dimensions:dict = dict([(col, i) for i, col in enumerate(dimensions)])
        self.measures:dict = dict([(col, i) for i, col in enumerate(measures)])
        self.values: list = [df[c].values for c in self.measures.keys()]  # value vectors (references only)
        self.cache: dict = {"@":0} if caching else None
        self.bitmaps: list = []  # bitmaps per dimension per member containing the row ids of the DataFrame
        for col in self.dimensions.keys():
            member_bitmaps = {}
            for row, member in enumerate(df[col].to_list()):
                if member not in member_bitmaps:
                    member_bitmaps[member] = BitMap([row])
                else:
                    member_bitmaps[member].add(row)

            for v in member_bitmaps.keys():
                member_bitmaps[v] = np.array(member_bitmaps[v].to_array())

            self.bitmaps.append(member_bitmaps)

    def get(self, *args, **kwargs):
        """
        Get the aggregated values for the given dimensions and members.

        :param kwargs: the dimension column names as keyword and their requested members as argument.
        :param args: (optional) some measure column names to be returned.
        :return:
            The aggregated values as:
            - a dict of (measures, value) pairs for all defined measures.
            - a scalar if only one measure as arg is given.
            - a list of values for multiple measures if multiple args are given.
        """
        if self.cache:
            key = f"{args}-{kwargs}"
            if key in self.cache:
                return self.cache[key]
        bitmaps = [(reduce(lambda x, y: snp.merge(x, y, duplicates=snp.MergeDuplicates.DROP), [self.bitmaps[d][m] for m in kwargs[dim]])
                   if (isinstance(kwargs[dim], list) or isinstance(kwargs[dim], tuple)) and not isinstance(kwargs[dim], str)
                   else self.bitmaps[d][kwargs[dim]]) for d, dim in enumerate(self.dimensions.keys()) if dim in kwargs]

        # sort from shortest to largest size to increase set intersection performance
        bitmaps = sorted(bitmaps, key=lambda l: len(l))

        records = reduce(lambda x, y: snp.intersect(x, y, duplicates=snp.IntersectDuplicates.DROP), bitmaps) if bitmaps else False
        if len(args) == 0: # return all totals as a dict
            result = dict([(c, np.nansum(self.values[i][records]).item()) if len(records) else(c, np.nansum(self.values[i]).item()) for c, i in self.measures.items()])
        elif len(args) == 1: # return total as scalar
            result = np.nansum(self.values[self.measures[args[0]]][records] if len(records) else self.values[self.measures[args[0]]]).item()
        else:
            result = [np.nansum(self.values[self.measures[a]][records] if len(records) else self.values[self.measures[a]]).item() for a in args] # return totals as a list
        if self.cache:
            self.cache[key] = result
        return result