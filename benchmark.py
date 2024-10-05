# nanocube - Copyright (c)2024, Thomas Zeutschler, MIT license
import random
import timeit
import string
from datetime import datetime, date, timedelta
import pandas as pd
from nanocube import NanoCube


# Pandas vs. NanoCube for OLAP queries
# --------------------------------
rows = 1_000_000
loops = 10

# Create a larger dataframe with 1M records
print(f"Creating Dataframe with {rows:,} rows and 5 columns ", end="")
start = datetime.now()
customers = string.ascii_uppercase
df = pd.DataFrame({'customer': random.choices(customers, weights=range(len(customers), 0, -1), k=rows),  # 'A', 'B', 'C', ...
                   'product':  random.choices([f'P{i}' for i in range(100)], weights=range(100, 0, -1), k=rows),  # 'P1', 'P2', 'P3', ...
                   'destination': random.choices([f'D{i}' for i in range(100)], weights=range(100, 0, -1), k=rows),  # 'D1', 'D2', 'D3', ...
                   'promo':    random.choices([True, False], k=rows),
                   'sales':    [int(random.random()*100) for _ in range(rows)],
                   'cost':     [int(random.random()*100) for _ in range(rows)]})
print(f"in {(datetime.now() - start).total_seconds():.5f} sec.")
print (df.head())

# Create a cube
print(f"\nCreating and preparing NanoCube from Dataframe ", end="")
start = datetime.now()
cube = NanoCube(df)
print(f"in {(datetime.now() - start).total_seconds():.5f} sec.")


# OLAP query using Pandas dataframe
q1 = 'df[(df["customer"] == "A") & (df["product"] == "P1")][["sales", "cost"]].sum()'
print(f"\nRunning OLAP-Queries with Pandas. Please wait...")
print(f"\tQuery 1: {q1}")
print(f"\tResult: {dict(df[(df['customer'] == 'A') & (df['product'] == 'P1')][['sales', 'cost']].sum().items())}")
q1_pd = timeit.timeit(q1, globals=globals(), number=loops)
print(f"\t{loops}x queries executed in {q1_pd:.5f} sec, avg. {q1_pd/loops:.5f} sec/query")

# OLAP query using NanoCube
q1 = 'cube.get(customer="A", product="P1")'
print(f"\nRunning OLAP-Queries with NanoCube. Don't wait...")
print(f"\tQuery 1: {q1}")
print(f"\tResult: {cube.get(customer='A', product='P1')}")
q1_cube = timeit.timeit(q1, globals=globals(), number=loops)
print(f"\t{loops}x queries executed in {q1_cube:.5f} sec, avg. {q1_cube/loops:.5f} sec/query")

print(f"\nBelieve it or not: Using NanoCube is {q1_pd/q1_cube:.0f}x times faster than Pandas DataFrame.")

print("*"*80)