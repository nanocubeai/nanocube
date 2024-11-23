# nanocube - Copyright (c)2024, Thomas Zeutschler, MIT license
import json
from array import array
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_bool_dtype, is_float_dtype
from pyroaring import BitMap

from nanocube.schema import Schema
from nanocube.nano_index import NanoIndex, NanoRoaringIndex, NanoNumpyIndex, IndexingMethod
import lz4.frame
import zstandard as zstd


import pyarrow as pa
import pyarrow.parquet as pq


class NanoCube:
    def __init__(self, df: pd.DataFrame, dimensions: list | None = None, measures:list | None = None,
                 caching: bool = True, indexing_method: IndexingMethod | str = IndexingMethod.roaring):
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
        >>> c_roaring = NanoCube(df)
        >>> print(c_roaring.get(customer='A', product='P1'))  # [100, 60]
        >>> print(c_roaring.get(customer='A'))                # [900, 420]
        >>> print(c_roaring.get(promo=True))                  # [800, 380]
        >>> print(c_roaring.get(promo=True))                  # [800, 380]
        """
        #self.schema = Schema(df=df, dimensions=dimensions, measures=measures)

        self._agg_func: dict = {
            "sum": np.nansum,
            "mean": np.nanmean,
            "min": np.nanmin,
            "max": np.nanmax,
            "std": np.nanstd,
            "var": np.nanvar,
            "count": np.count_nonzero,
        }

        measures = [c for c in df.columns if is_numeric_dtype(df[c].dtype) and not is_bool_dtype(df[c].dtype)] if measures is None else measures
        self.measures:dict = dict([(col, i) for i, col in enumerate(measures)])

        dimensions = [c for c in df.columns if not c in measures and not is_float_dtype(df[c].dtype)] if dimensions is None else dimensions
        self.indexing_method: IndexingMethod = IndexingMethod.from_str(indexing_method)
        self.index:NanoIndex = NanoIndex.create(df=df, dimensions=dimensions, indexing_method=self.indexing_method)
        self.dimensions:dict = self.index._dimensions

        self.values: list = [df[c].to_numpy() for c in self.measures.keys()]  # value vectors (references only)
        self.caching:bool = caching
        self.cache: dict = {"@":0} if caching else None

        compressor = "zstd"  # zstd, lz4, snappy, zlib, blosc, brotli, lzf, lzma, zstd, snappy, bzip2, gif
        if compressor == "lz4":
            self._compress = lz4.frame.compress
            self._decompress = lz4.frame.decompress
        elif compressor == "zstd":
            self._compress = zstd.ZstdCompressor(level=3).compress
            self._decompress = zstd.ZstdDecompressor().decompress


    def get(self, *args, aggregate: str | None = "sum",  **kwargs):
        """
        Get the aggregated values for the given dimensions and members.

        :param aggregate: the aggregation function to be used (sum, mean, min, max, std, var, count).
        :param kwargs: the dimension column names as keyword and their requested members as argument.
        :param args: (optional) some measure column names to be returned.
        :return:
            The aggregated values as:
            - a dict of (measures, value) pairs for all defined measures.
            - a scalar if only one measure as arg is given.
            - a list of values for multiple measures if multiple args are given.
        """

        if self.caching:
            key = f"{args}-{kwargs}"
            if key in self.cache:
                return self.cache[key]

        rows = self.index.get_rows(**kwargs)
        agg_func = self._agg_func[aggregate]  # if aggregate in self._agg_func else np.nansum

        if isinstance(rows, array | np.ndarray) and len(rows) > 0:
            if len(args) == 0:  # return all measures as dict
                result = dict([(c, agg_func(self.values[i][rows]).item()) for c, i in self.measures.items()])
            elif len(args) == 1:  # return one measure as scalar value
                result = agg_func(self.values[self.measures[args[0]]][rows]).item()
            else:  # return list of measures
                result = [agg_func(self.values[self.measures[a]][rows]) for a in args]
        elif not rows:  # no rows available for the given context
            result = 0
        else: # rows == True -> return all rows
            if len(args) == 0:
                result = dict([(c, agg_func(self.values[i]).item()) for c, i in self.measures.items()])
            elif len(args) == 1:
                result = agg_func(self.values[self.measures[args[0]]]).item()
            else:
                result = [agg_func(self.values[self.measures[a]]).item() for a in args]

        if self.caching:
            self.cache[key] = result
        return result

    @staticmethod
    def load(file_name: str) -> 'NanoCube':
        """
        Load a NanoCube from a file.
        """
        # Read from Parquet
        table = pq.read_table(file_name)

        # Deserialize metadata
        bin_data = table[0].to_pylist()
        meta = json.loads(bin_data[0])

        method = meta["indexing_method"]
        indexing_method = IndexingMethod.from_str(method)
        nc = NanoCube(pd.DataFrame(), indexing_method=indexing_method)

        nc.index._dimensions = meta["dimensions"]
        nc.dimensions = meta["dimensions"]
        nc.measures = meta["measures"]
        nc.values = meta["values"]
        value_types = meta["value_types"]
        nc.index._bitmaps = [dict([(m, i) for m, i in bm.items()]) for bm in meta["members"]]

        # Deserialize bitmaps
        if indexing_method == IndexingMethod.roaring:
            for d, bm_dict in enumerate(nc.index._bitmaps):
                for m, i in bm_dict.items():
                    nc.index._bitmaps[d][m] = BitMap.deserialize(nc._decompress(bin_data[i]))
        elif indexing_method == IndexingMethod.numpy:
            for d, bm_dict in enumerate(nc.index._bitmaps):
                for m, i in bm_dict.items():
                    data = BitMap.deserialize(nc._decompress(bin_data[i])).to_array()
                    nc.index._bitmaps[d][m] = np.array(data)
        else:
            raise ValueError(f"Unsupported indexing method {indexing_method}")

        # Deserialize values
        for i, v in enumerate(nc.values):
            value_type = value_types[i]
            if value_type == 'float64':
                type = np.float64
            elif value_type == 'int64':
                type = np.int64
            else:
                raise ValueError(f"Unsupported value type {value_type}")
            nc.values[i] = np.frombuffer(nc._decompress(bin_data[v]), dtype=type)

        return nc


    def save(self, file_name: str):
        """
        Save the NanoCube to a file.
        """
        # Create Arrow schema
        schema = pa.schema([
            pa.field('data', pa.binary())],
            metadata={"app": "NanoCube", "version": "0.1.2"})

        # Serialize metadata
        meta = {"rows": len(self.values[0]), "dimensions": self.dimensions, "measures": self.measures,
                "members": [dict([(m, -1) for m in bm.keys()]) for bm in self.index._bitmaps],
                "values": [-1 for _ in self.values],
                "value_types": [f"{type(v[0]).__name__}" for v in self.values],
                "indexing_method": str(self.indexing_method)}
        bin_data = [None, ]
        z = 1

        # Serialize bitmaps
        if self.indexing_method == IndexingMethod.roaring:
            for i, bm_dict in enumerate(self.index._bitmaps):
                for j, bm in enumerate(bm_dict.values()):
                    bin_data.append(self._compress(bm.serialize()))
                meta["members"][i].update({m: z + j for j, m in enumerate(bm_dict.keys())})
                z += len(bm_dict)
        elif self.indexing_method == IndexingMethod.numpy:
            for i, bm_dict in enumerate(self.index._bitmaps):
                for j, bm in enumerate(bm_dict.values()):
                    bin_data.append(self._compress(BitMap(bm).serialize()))
                meta["members"][i].update({m: z + j for j, m in enumerate(bm_dict.keys())})
                z += len(bm_dict)
        else:
            raise ValueError(f"Unsupported indexing method {self.indexing_method}")

        # Serialize values
        for i, v in enumerate(self.values):
            bin_data.append(self._compress(v.tobytes()))
            meta["values"][i] = z + i

        # Serialize metadata
        bin_data[0] = json.dumps(meta).encode('utf-8')

        # write to disk
        data = [pa.array(bin_data, type=pa.binary()), ]
        pat = pa.Table.from_arrays(data, schema=schema)
        pq.write_table(pat, file_name)
