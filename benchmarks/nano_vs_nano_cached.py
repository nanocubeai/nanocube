from nanocube import NanoCube
import duckdb
import pandas as pd
from timeit import timeit
from pathlib import Path
import os

# Create a DataFrame and NanoCube
file_car_prices = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.parquet"
df = pd.read_parquet(file_car_prices)
#df.sort_values(by=['body', 'make', 'model', 'trim'], inplace=True)
nc = NanoCube(df, dimensions=['make', 'model', 'trim', 'body'], measures=['mmr'], caching=False)
nc_cached = NanoCube(df, dimensions=['make', 'model', 'trim', 'body'], measures=['mmr'], caching=True)


def query_nanocube(loops=1000):
    value = 0
    for _ in range(loops):
        value += nc.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')
    return value

def query_nanocube_cached(loops=1000):
    value = 0
    for _ in range(loops):
        value += nc_cached.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')
    return value


if __name__ == '__main__':
    ncc_time = timeit(query_nanocube_cached, number=1)
    nc_time = timeit(query_nanocube, number=1)
    print(f"NanoCube point query in {nc_time:.5f} sec.")
    print(f"NanoCube(cached) point query in {ncc_time:.5f} sec.")
    print(f"NanoCube cached is {nc_time/ncc_time:.2f}x times faster "
          f"vs. uncached on recurring queries with {1000/ncc_time:,.0f} q/sec.")
    print(f"\tns.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')")
    assert(query_nanocube() == query_nanocube_cached())
