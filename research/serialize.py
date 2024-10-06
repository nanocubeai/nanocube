# Some Research on How to Serialize NanoCubes
import json
import random
from datetime import datetime

import numpy as np
import pandas as pd
from string import ascii_uppercase

import pyarrow as pa
import pyarrow.parquet as pq
from pyroaring import BitMap

from nanocube import NanoCube


def create_df(dim_cols, msr_cols, rows, sorted: bool=True):
    # creates a random dataframe with dimensions and measures
    def mn(n):
        d, m = divmod(n, 26)
        return '' if n < 0 else mn(d - 1) + chr(m + 65)
    df_dim = pd.DataFrame([[mn(random.randint(0, 2 + (x +1)**2)) for x in range(dim_cols)] for _ in range(rows)], columns=[f"dim{x}" for x in list(ascii_uppercase)[:dim_cols]])
    # df_msr = pd.DataFrame(np.ones(shape=(rows, msr_cols), dtype=np.float64), columns=[f"dim{x}" for x in list(ascii_uppercase)[dim_cols:dim_cols+msr_cols]])
    df_msr = pd.DataFrame([[round(random.random() * 10_000, 2)  for x in range(msr_cols)] for _ in range(rows)], columns=[f"dim{x}" for x in list(ascii_uppercase)[dim_cols:dim_cols+msr_cols]])
    df = pd.concat([df_dim, df_msr], axis=1)
    if sorted:
        df.sort_values(df.columns.tolist(), inplace=True)
    return df


def serialize_nano(nc, filename):
    # Create Arrow schema
    schema = pa.schema([
        pa.field('data', pa.binary())],
        metadata={"app": "NanoCube", "version": "0.1.2"})
    # Serialize metadata
    meta = {"rows": len(nc.values[0]), "dimensions": nc.dimensions, "measures": nc.measures,
            "members": [dict([(m,-1) for m in bm.keys()]) for bm in nc.bitmaps],
            "values": [-1 for _ in nc.values],
            "value_types": [f"{type(v[0]).__name__}" for v in nc.values]}
    bin_data = [None,]
    z=1
    for i, bm_dict in enumerate(nc.bitmaps):
        for j, bm in enumerate(bm_dict.values()):
            bin_data.append(bm.serialize())
        meta["members"][i].update({m: z + j for j, m in enumerate(bm_dict.keys())})
        z += len(bm_dict)
    for i, v in enumerate(nc.values):
        bin_data.append(v.tobytes())
        meta["values"][i] = z + i

    # Serialize metadata
    bin_data[0] = json.dumps(meta).encode('utf-8')
    # write to disk
    data = [pa.array(bin_data, type=pa.binary()), ]
    pat = pa.Table.from_arrays(data, schema=schema)
    pq.write_table(pat, 'files/nanocube.parquet')

def deserialize_nano(file_name) -> NanoCube:

    # Read from Parquet
    table = pq.read_table(file_name)

    # Deserialize metadata
    bin_data = table[0].to_pylist()
    meta = json.loads(bin_data[0])
    nc = NanoCube(pd.DataFrame())
    nc.dimensions = meta["dimensions"]
    nc.measures = meta["measures"]
    nc.values = meta["values"]
    value_types = meta["value_types"]
    nc.bitmaps = [dict([(m, i) for m, i in bm.items()]) for bm in meta["members"]]
    # Deserialize bitmaps
    for d, bm_dict in enumerate(nc.bitmaps):
        for m, i in bm_dict.items():
            nc.bitmaps[d][m] = BitMap.deserialize(bin_data[i])
    # Deserialize values
    for i, v in enumerate(nc.values):
        value_type = value_types[i]
        if value_type == 'float64':
            type = np.float64
        elif value_type == 'int64':
            type = np.int64
        else:
            raise ValueError(f"Unsupported value type {value_type}")
        nc.values[i] = np.frombuffer(bin_data[v], dtype=type)

    return nc

if __name__ == '__main__':

    # Create a DataFrame
    df = create_df(5,2,100_000, False)

    # Serialize DataFrame to Parquet
    start = datetime.now()
    df.to_parquet('files/df.parquet')
    duration = (datetime.now() - start).total_seconds()
    print(f"Serialized dataframe to Parquet in {duration:.5f} sec.")

    # Deserialize DataFrame from Parquet
    start = datetime.now()
    df2 = pd.read_parquet('files/df.parquet')
    duration = (datetime.now() - start).total_seconds()
    print(f"Deserialized dataframe from Parquet in {duration:.5f} sec.")

    nc = NanoCube(df)

    # Serialize NanoCube to Parquet
    start = datetime.now()
    serialize_nano(nc, 'files/nanocube.parquet')
    duration = (datetime.now() - start).total_seconds()
    print(f"Serialized NanoCube to Parquet in {duration:.5f} sec.")

    # Deserialize NanoCube from Parquet
    start = datetime.now()
    nc2 = deserialize_nano('files/nanocube.parquet')
    duration = (datetime.now() - start).total_seconds()
    print(f"Deserialized NanoCube to Parquet in {duration:.5f} sec.")

    # Ensure the two NanoCubes are identical
    assert(nc.get() == nc2.get())
    assert(nc.get(dimA='A', dimB='B') == nc2.get(dimA='A', dimB='B'))
    assert(nc.get(dimA='A', dimB='B', dimc='C') == nc2.get(dimA='A', dimB='B', dimc='C'))
