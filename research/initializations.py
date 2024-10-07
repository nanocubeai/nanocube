# importing libraries
from pathlib import Path
import os
import pandas as pd
from nanocube import NanoCube
import polars as pl
import duckdb
import sqlite3

# Create a DataFrame and NanoCube
file_car_prices = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.parquet"
df = pd.read_parquet(file_car_prices) #.head(100_000)
nc = NanoCube(df,
              dimensions=['year', 'make', 'model', 'trim', 'body', 'transmission', 'vin',
                              'state', 'condition', 'color', 'interior', 'seller', 'saledate'],
              measures=['odometer', 'mmr', 'sellingprice'])
print(df.shape)
