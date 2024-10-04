# nanocube - Copyright (c)2024, Thomas Zeutschler, MIT license
from functools import reduce
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_bool_dtype, is_float_dtype
from pyroaring import BitMap

__author__ = "Thomas Zeutschler"
__version__ = "0.1.1"
__license__ = "MIT"
VERSION = __version__

__all__ = [
    "Cube",
]


class Cube:
    """
    A super minimalistic (27 lines of code) in-memory OLAP cube implementation for lightning fast point queries
    upon Pandas DataFrames (100x to 1000x times faster than Pandas). By default, all non-numeric columns will be
    used as dimensions and all numeric columns as measures. Roaring Bitmaps (https://roaringbitmap.org) are used
    to construct and query a multi-dimensional cube, Numpy is used for aggregations.
    """
    def __init__(self, df: pd.DataFrame, dimensions: list | None = None, measures:list | None = None):
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

        Examples
        --------
        >>> import pandas as pd
        >>> from nanocube import Cube
        >>> # Create a DataFrame
        >>> df = pd.DataFrame({'customer': [ 'A',  'B',  'A',  'B',  'A'],
        >>>                    'product':  ['P1', 'P2', 'P3', 'P1', 'P2'],
        >>>                    'promo':    [True, False, True, True, False],
        >>>                    'sales':    [ 100,  200,  300,  400,  500],
        >>>                    'cost':     [  60,   90,  120,  200,  240]})
        >>> # Convert to a Cube
        >>> cube = Cube(df)
        >>> print(cube.get(customer='A', product='P1'))  # [100, 60]
        >>> print(cube.get(customer='A'))                # [900, 420]
        >>> print(cube.get(promo=True))                  # [800, 380]
        >>> print(cube.get(promo=True))                  # [800, 380]
        """
        self.df = df
        measures = [c for c in df.columns if is_numeric_dtype(df[c].dtype) and not is_bool_dtype(df[c].dtype)] if measures is None else measures
        dimensions = [c for c in df.columns if not c in measures and not is_float_dtype(df[c].dtype)] if dimensions is None else dimensions
        self.dimensions:dict = dict([(col, i) for i, col in enumerate(dimensions)])
        self.measures:dict = dict([(col, i) for i, col in enumerate(measures)])
        self.values: list = [df[c].values for c in self.measures.keys()]  # value vectors (references only)
        self.bitmaps: list = []  # bitmaps per dimension per member containing the row ids of the DataFrame
        for col in self.dimensions.keys():
            members, records = np.unique(df[col], return_inverse=True)
            self.bitmaps.append(dict([(m, BitMap(np.where(records == i)[0])) for i, m in enumerate(members)]))

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
        bitmaps = [(reduce(lambda x, y: x | y, [self.bitmaps[d][m] for m in kwargs[dim]])
                   if (isinstance(kwargs[dim], list) or isinstance(kwargs[dim], tuple)) and not isinstance(kwargs[dim], str)
                   else self.bitmaps[d][kwargs[dim]]) for d, dim in enumerate(self.dimensions.keys()) if dim in kwargs]
        records = reduce(lambda x, y: x & y, bitmaps) if bitmaps else False
        if len(args) == 0: # return all totals as a dict
            return dict([(c, np.sum(self.values[i][records]).item()) if records else(c, np.sum(self.values[i]).item()) for c, i in self.measures.items()])
        elif len(args) == 1: # return total as scalar
            return np.sum(self.values[self.measures[args[0]]][records] if records else self.values[self.measures[args[0]]]).item()
        return [np.sum(self.values[self.measures[a]][records] if records else self.values[self.measures[a]]).item() for a in args] # return totals as a list
