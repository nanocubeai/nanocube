# Some Research on How to Serialize NanoCubes
import random
from datetime import datetime
import pandas as pd
from string import ascii_uppercase
from nanocube import NanoCube


def create_df(dim_cols, msr_cols, rows, sorted: bool=True):
    # creates a random dataframe with dimensions and measures
    def mn(n):
        d, m = divmod(n, 26)
        return '' if n < 0 else mn(d - 1) + chr(m + 65)
    df_dim = pd.DataFrame([[mn(random.randint(0, 2 + (x +1)**2)) for x in range(dim_cols)] for _ in range(rows)], columns=[f"dim{x}" for x in list(ascii_uppercase)[:dim_cols]])
    df_msr = pd.DataFrame([[round(random.random() * 10_000, 2)  for x in range(msr_cols)] for _ in range(rows)], columns=[f"dim{x}" for x in list(ascii_uppercase)[dim_cols:dim_cols+msr_cols]])
    df = pd.concat([df_dim, df_msr], axis=1)
    if sorted:
        df.sort_values(df.columns.tolist(), inplace=True)
    return df


if __name__ == '__main__':

    rows = 100_000
    sorted = True

    # Create a DataFrame
    df = create_df(5,2,rows, sorted)
    ncr = NanoCube(df, indexing_method='roaring')
    ncn = NanoCube(df, indexing_method='numpy')

    # Serialize *************************************************
    # DataFrame
    start = datetime.now()
    df.to_parquet('files/df.parquet')
    duration = (datetime.now() - start).total_seconds()
    print(f"Serialized dataframe in {duration:.5f} sec.")

    # NanoCube Roaring
    start = datetime.now()
    ncr.save('files/roaring.nano')
    duration = (datetime.now() - start).total_seconds()
    print(f"Serialized NanoCube Roaring in {duration:.5f} sec.")

    # NanoCube Numpy
    start = datetime.now()
    ncn.save('files/numpy.nano')
    duration = (datetime.now() - start).total_seconds()
    print(f"Serialized NanoCube Numpy in {duration:.5f} sec.")


    # DeSerialize ***********************************************
    # DataFrame
    start = datetime.now()
    dfd = pd.read_parquet('files/df.parquet')
    duration = (datetime.now() - start).total_seconds()
    print(f"Deserialized dataframe in {duration:.5f} sec.")

    # NanoCube Roaring
    start = datetime.now()
    ncrd = NanoCube.load('files/roaring.nano')
    duration = (datetime.now() - start).total_seconds()
    print(f"Deserialized NanoCube Roaring in {duration:.5f} sec.")

    # NanoCube Numpy
    start = datetime.now()
    ncnd = NanoCube.load('files/numpy.nano')
    duration = (datetime.now() - start).total_seconds()
    print(f"Deserialized NanoCube Numpy in {duration:.5f} sec.")


    # Validation ***********************************************
    assert(ncr.get() == ncrd.get())
    assert(ncr.get(dimA='A', dimB='B') == ncrd.get(dimA='A', dimB='B'))
    assert(ncr.get(dimA='A', dimB='B', dimc='C') == ncrd.get(dimA='A', dimB='B', dimc='C'))

    assert(ncn.get() == ncnd.get())
    assert(ncn.get(dimA='A', dimB='B') == ncnd.get(dimA='A', dimB='B'))
    assert(ncn.get(dimA='A', dimB='B', dimc='C') == ncnd.get(dimA='A', dimB='B', dimc='C'))
