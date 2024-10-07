from nanocube import NanoCube
import duckdb
import pandas as pd
from timeit import timeit
from pathlib import Path
import os


# Create a DataFrame and NanoCube
file_car_prices = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.parquet"
df = pd.read_parquet(file_car_prices)
ns = NanoCube(df, dimensions=['make', 'model', 'trim', 'body'], measures=['mmr'])

# Create a DuckDB table
duckdb.sql(f"CREATE TABLE car_prices AS SELECT * FROM '{file_car_prices}'")


def query_nanocube(loops=1000):
    value = 0
    for _ in range(loops):
        value += ns.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')
    return value

def query_duckdb(loops=1000):
    value = 0
    for _ in range(loops):
        value += duckdb.sql("SELECT SUM(mmr) FROM car_prices WHERE model='Optima' AND trim='LX' AND make='Kia' AND body='Sedan';").fetchall()[0][0]
    return value


if __name__ == '__main__':
    pl_time = timeit(query_duckdb, number=1)
    nc_time = timeit(query_nanocube, number=1)
    print(f"DuckDB point query in {pl_time:.5f} sec.")
    print(f"NanoCube point query in {nc_time:.5f} sec.")
    print(f"NanoCube is {pl_time/nc_time:.2f}x times faster than DuckDB on query with 4 filters on 1 measure:")
    print(f"\tns.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')")
    assert(query_nanocube() == query_duckdb())
