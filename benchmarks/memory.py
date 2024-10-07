# importing libraries
from pathlib import Path
import os
import pandas as pd
from nanocube import NanoCube
import polars as pl
import duckdb
import sqlite3
from memory_profiler import profile


# Create a DataFrame and NanoCube
file_car_prices = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.parquet"
df = pd.read_parquet(file_car_prices)


@profile
def baseline():
    return 1

@profile
def pandas_dataframe():
    df = pd.read_parquet(file_car_prices)
    return df

@profile
def nanocube():
    nc = NanoCube(df,
                  dimensions=['year', 'make', 'model', 'trim', 'body', 'transmission', 'vin',
                                  'state', 'condition', 'color', 'interior', 'seller', 'saledate'],
                  measures=['odometer', 'mmr', 'sellingprice'])
    return nc

@profile
def polars_table():
    df = pl.read_parquet(file_car_prices)
    return df

@profile
def duckdb_table():
    duckdb.sql(f"CREATE TABLE car_prices AS SELECT * FROM '{file_car_prices}'")
    return duckdb

@profile
def sqlite_table():
    conn = sqlite3.connect(':memory:')
    df.to_sql('car_prices', conn, index=False)
    cursor = conn.cursor()
    return conn

@profile
def sqlite_table_indexed():
    conn = sqlite3.connect(':memory:')
    df.to_sql('car_prices', conn, index=False)
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX index_car_prices ON car_prices (make, model, trim, body);")
    return conn


if __name__ == '__main__':
    # Memory utilization comparison
    baseline()
    pandas_dataframe()
    nanocube()
    polars_table()
    duckdb_table()
    sqlite_table()
    sqlite_table_indexed()




