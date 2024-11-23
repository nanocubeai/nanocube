import nanocube
from nanocube import NanoCube

import numpy as np
import pandas as pd
from numpy import ndarray
from timeit import timeit
from pathlib import Path
import os

print(f"NanoCube version: {nanocube.__version__}")
print(f"Numpy version: {np.version.version}")
file_car_prices = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.parquet"
file_car_prices_nano = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.nano"

# Create a DataFrame and NanoCube
nc:NanoCube|None = None

df:pd.DataFrame = pd.DataFrame()
mask:np.ndarray = np.array([])

def pandas_load():
    global df, mask

    df = pd.read_parquet(file_car_prices)
    mask = np.random.choice(np.arange(0, len(df.index)), replace=False, size=(len(df.index)//10))

def nano_from_dataframe_load():
    global df, nc
    nc = NanoCube(df, dimensions=['make', 'model', 'trim', 'body'], measures=['mmr'], caching=False,
                  indexing_method='roaring')

def nano_save():
    global df, nc
    nc.save(str(file_car_prices_nano))

def nano_load():
    global df, nc
    nc = NanoCube.load(str(file_car_prices_nano))

def numpy_sort():
    global df
    df.sort_values(by=['model', 'make', 'trim', 'body'], inplace=True)

def query_nanocube(loops=1000):
    value = 0
    for _ in range(loops):
        value += nc.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')
        #value += nc.get('mmr', make='Kia')
    return value

def pandas_flat_sum(loops=1000):
    value = 0
    for _ in range(loops):
        value += df['mmr'].sum()
    return value
def numpy_flat_sum(loops=1000):
    value = 0
    array = df['mmr'].to_numpy()
    for _ in range(loops):
        value += array.sum()
    return value
def numpy_masked_sum(loops=1000):
    value = 0
    array = df['mmr'].to_numpy()
    for _ in range(loops):
        value += array[mask].sum()
    return value


if __name__ == '__main__':
    loops = 1000
    nc_time= timeit(pandas_load, number=1)
    print(f"Pandas load file in {nc_time:.5f} sec.")

    nc_time= timeit(numpy_sort, number=1)
    print(f"Numpy sort in {nc_time:.5f} sec.")

    nc_time= timeit(nano_from_dataframe_load, number=1)
    print(f"Load NanoCube from Dataframe in {nc_time:.5f} sec.")

    nc_time= timeit(nano_save, number=1)
    print(f"NanoCube save() in {nc_time:.5f} sec.")

    nc_time= timeit(nano_load, number=1)
    print(f"NanoCube load() in {nc_time:.5f} sec.")

    nano_from_dataframe_load()

    nc_time= timeit(query_nanocube, number=1)
    print(f"NanoCube {loops}x point queries in {nc_time:.5f} sec., {loops/nc_time:.0f} queries/sec.")
    print(f"\tns.get('mmr',  make='Kia', model='Optima', trim='LX', body='Sedan')")

    records = len(df['mmr'].to_numpy())
    pandas_time = timeit(pandas_flat_sum, number=1)
    print(f"\nPandas {loops}x flat sum in {pandas_time:.5f} sec., "
          f"{loops/pandas_time:.0f} queries/sec.,"
          f" {loops * records / 1_000_000 / pandas_time:.0f}M aggs/sec.")

    numpy_time = timeit(numpy_flat_sum, number=1)
    print(f"Numpy {loops}x flat sum in {numpy_time:.5f} sec., "
          f"{loops/numpy_time:.0f} queries/sec."
          f" {loops * records / 1_000_000 / numpy_time:.0f}M aggs/sec.")

    numpy_time = timeit(numpy_masked_sum, number=1)
    print(f"Numpy {loops}x masked sum in {numpy_time:.5f} sec., "
          f"{loops/numpy_time:.0f} queries/sec."
          f" {loops * len(mask) / 1_000_000 / numpy_time:.0f}M aggs/sec.")