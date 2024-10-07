from nanocube import NanoCube
import pandas as pd
import sqlite3
from timeit import timeit
from pathlib import Path
import os


# Create a DataFrame and NanoCube
file_car_prices = Path(os.path.dirname(os.path.realpath(__file__))) / "files" / "car_prices.parquet"
df = pd.read_parquet(file_car_prices)
ns = NanoCube(df, dimensions=['make', 'model', 'trim', 'body'], measures=['mmr'])

# Connect to in-memory SQLite database
conn = sqlite3.connect(':memory:')
df.to_sql('car_prices', conn, index=False)
cursor = conn.cursor()
if True:
    cursor.execute("CREATE INDEX index_car_prices ON car_prices (make, model, trim, body);")


def query_nanocube(loops=1000):
    value = 0
    for _ in range(loops):
        value += ns.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')
    return value

def query_sqlite(loops=1000):
    value = 0
    sql = "SELECT SUM(mmr) FROM car_prices WHERE model='Optima' AND trim='LX' AND make='Kia' AND body='Sedan';"
    for _ in range(loops):
        cursor.execute(sql)
        result = cursor.fetchone()[0]
        value += result
    return value


if __name__ == '__main__':
    pl_time = timeit(query_sqlite, number=1)
    nc_time = timeit(query_nanocube, number=1)
    print(f"SQLite point query in {pl_time:.5f} sec.")
    print(f"NanoCube point query in {nc_time:.5f} sec.")
    print(f"NanoCube is {pl_time/nc_time:.2f}x times faster than SQLite on query with 4 filters on 1 measure:")
    print(f"\tns.get('mmr', model='Optima', trim='LX', make='Kia', body='Sedan')")
    assert(query_nanocube() == query_sqlite())

    # Close the connection
    conn.close()
