from timeit import timeit
from pathlib import Path
import os

import pandas as pd
from duckdb.duckdb import query

from nanocube import NanoCube

import duckdb
import polars as pl
import sqlite3
import pyarrow as pa
import pyarrow.compute as pc



    

# Initialize DataFrame
file_car_prices = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.parquet"
df = pd.read_parquet(file_car_prices)
df.sort_values(by=[ 'body', 'make', 'model', 'trim',], inplace=True)

# Initialize NanoCube
nc = NanoCube(df, dimensions=['make', 'model', 'trim', 'body'], measures=['mmr'], caching=False, indexing_method='roaring')

# Initialize DuckDB
duckdb.sql(f"CREATE TABLE car_prices AS SELECT * FROM '{file_car_prices}'")

# Initialize Polars
dfp = pl.from_pandas(df)

# Initialize SQLite (no index)
conn = sqlite3.connect(':memory:')
df.to_sql('car_prices', conn, index=False)
cursor = conn.cursor()

# Initialize SQLite (no index)
conn_idx = sqlite3.connect(':memory:')
df.to_sql('car_prices', conn_idx, index=False)
cursor_idx = conn_idx.cursor()
cursor_idx.execute("CREATE INDEX index_car_prices ON car_prices (make, model, trim, body);")

# Initialize Arrow
pat = pa.Table.from_pandas(df)


def query_pandas(loops=1000):
    value = 0
    for _ in range(loops):
        value += df[(df['make'] == 'Kia') & (df['model'] == 'Optima') & (df['trim'] == 'LX') & (df['body'] == 'Sedan')]['mmr'].sum()
    return value

def query_nanocube(loops=1000):
    value = 0
    for _ in range(loops):
        value += nc.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')
    return value

def query_duckdb(loops=1000):
    value = 0
    for _ in range(loops):
        value += duckdb.sql("SELECT SUM(mmr) FROM car_prices WHERE model='Optima' AND trim='LX' AND make='Kia' AND body='Sedan';").fetchall()[0][0]
    return value

def query_polars(loops=1000):
    value = 0
    for _ in range(loops):
        value += dfp.filter(pl.col('make') == 'Kia', pl.col('model') == 'Optima', pl.col('trim') == 'LX', pl.col('body') == 'Sedan')['mmr'].sum()
    return value

def query_sqlite(loops=1000):
    value = 0
    sql = "SELECT SUM(mmr) FROM car_prices WHERE model='Optima' AND trim='LX' AND make='Kia' AND body='Sedan';"
    for _ in range(loops):
        cursor.execute(sql)
        result = cursor.fetchone()[0]
        value += result
    return value

def query_sqlite_idx(loops=1000):
    value = 0
    sql = "SELECT SUM(mmr) FROM car_prices WHERE model='Optima' AND trim='LX' AND make='Kia' AND body='Sedan';"
    for _ in range(loops):
        cursor_idx.execute(sql)
        result = cursor_idx.fetchone()[0]
        value += result
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

    methods = {
        'Pandas': query_pandas,
        'DuckDB': query_duckdb,
        'Polars': query_polars,
        'SQLite': query_sqlite,
        'SQLite (indexed)': query_sqlite_idx,
        'NanoCube': query_nanocube,
        'Arrow': query_arrow
    }
    print ("Benchmarking NanoCube vs Others (please wait...)")
    print ("*"*50)
    print(f"\tDataset:     'car_prices_us.parquet' ({len(df.columns)} columns x {len(df):,} rows)")
    print(f"\tIterations:  1,000x queries per technology")
    print(f"\tFiltering:   4x columns (model='Optima', trim='LX', make='Kia', body='Sedan')")
    print(f"\tAggregation: sum() over column 'mmr'")

    results = {method: round(timeit(query, number=1), 3) for method, query in methods.items()}
    min_result = min(results.values())
    results = dict(sorted(results.items(), key=lambda x: x[1]))
    data = {"technology": list(results.keys()), "duration_sec": list(results.values()),
            "factor": [round(query/min_result,3) for query in results.values()]}
    print(pd.DataFrame(data).to_markdown())

    assert(query_nanocube() == query_duckdb())
