from nanocube import NanoCube
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc

from timeit import timeit
from pathlib import Path


import os

# Create a DataFrame and NanoCube
file_car_prices = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.parquet"
df = pd.read_parquet(file_car_prices)
df.sort_values(by=['model', 'make', 'trim', 'body'], inplace=True)


#df.sort_values(by=['body', 'make', 'model', 'trim'], inplace=True)
nc = NanoCube(df, dimensions=['make', 'model', 'trim', 'body'], measures=['mmr'], caching=False)

# Create a pyarrow table
pat = pq.read_table(file_car_prices)
pat.sort_by([('model', 'ascending') , ('make', 'ascending') , ('trim', 'ascending') , ('body', 'ascending')])


def query_nanocube(loops=1000):
    value = 0
    for _ in range(loops):
        value += nc.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')
    return value

def query_arrow(loops=1000):
    value = 0
    for _ in range(loops):
        criteria = [
            pc.equal(pat["model"], "Optima"),
            pc.equal(pat["trim"], "LX"),
            pc.equal(pat["make"], "Kia"),
            pc.equal(pat["body"], "Sedan"),
        ]
        combined_filter = criteria[0]
        for condition in criteria[1:]:
            combined_filter = pc.and_(combined_filter, condition)

        filtered_table = pat.filter(combined_filter)
        value += pc.sum(filtered_table['mmr']).as_py()

    return value


if __name__ == '__main__':

    loops = 1000
    pl_time = timeit(query_arrow, number=1)
    nc_time = timeit(query_nanocube, number=1)
    print(f"Arrow {loops}x point queries in {pl_time:.5f} sec, {loops/pl_time:.0f} queries/sec.")

    print(f"NanoCube {loops}x point queries in {nc_time:.5f} sec., {loops/nc_time:.0f} queries/sec.")
    print(f"NanoCube is {pl_time/nc_time:.2f}x times faster than Polars on query with 4 filters on 1 measure:")
    print(f"\tns.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')")
    assert(query_nanocube() == query_arrow())
