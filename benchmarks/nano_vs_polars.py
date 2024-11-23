from nanocube import NanoCube
import pandas as pd
import polars as pl
from timeit import timeit
from pathlib import Path


import os

# Create a DataFrame and NanoCube
file_car_prices = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.parquet"
df = pd.read_parquet(file_car_prices)
#df.sort_values(by=['body', 'make', 'model', 'trim'], inplace=True)
df.sort_values(by=['model', 'make', 'trim', 'body'], inplace=True)
nc = NanoCube(df, dimensions=['make', 'model', 'trim', 'body'], measures=['mmr'], caching=False)

# Create a Polars table
#df = pl.read_parquet(file_car_prices)
df = pl.from_pandas(df)



def query_nanocube(loops=1000):
    value = 0
    for _ in range(loops):
        value += nc.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')
    return value

def query_polars(loops=1000):
    value = 0
    for _ in range(loops):
        value += df.filter(pl.col('make') == 'Kia', pl.col('model') == 'Optima', pl.col('trim') == 'LX', pl.col('body') == 'Sedan')['mmr'].sum()
    return value


if __name__ == '__main__':

    loops = 1000
    pl_time = timeit(query_polars, number=1)
    nc_time = timeit(query_nanocube, number=1)
    print(f"Polars {loops}x point queries in {pl_time:.5f} sec, {loops/pl_time:.0f} queries/sec.")
    print(f"NanoCube {loops}x point queries in {nc_time:.5f} sec., {loops/nc_time:.0f} queries/sec.")
    print(f"NanoCube is {pl_time/nc_time:.2f}x times faster than Polars on query with 4 filters on 1 measure:")
    print(f"\tns.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')")
    assert(query_nanocube() == query_polars())
