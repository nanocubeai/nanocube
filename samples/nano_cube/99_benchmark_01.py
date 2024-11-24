# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
import gc
import random
import timeit

from nanocube import Cube, CachingStrategy
from datasets.datasets import car_sales

df, schema = car_sales()
use_schema = False
if use_schema:
    cube = Cube(df, schema=schema, caching=CachingStrategy.NONE)
else:
    cube = Cube(df, caching=CachingStrategy.NONE)

caching_strategy = CachingStrategy.LAZY
if use_schema:
    cached_cube = Cube(df, schema=schema, caching=caching_strategy)
else:
    cached_cube = Cube(df, caching=caching_strategy)

# get all car-makers (96 in total
makers = cube.make.members

address = "cube.make.BMW.sellingprice"
x, y, z = 0, 0, 0


def normal_read(make: str):
    value = cube.make[make].sellingprice
    return value


def cached_read(make: str):
    value = cached_cube.make[make].sellingprice
    return value


def df_read(make: str):
    value = df.loc[df['make'] == make, 'sellingprice'].sum()
    return value


# **********************
print("Performance comparison CubedPandas cube vs. Pandas dataframe:")
print("*" * 60)
loops = 1
records_total = len(cube)
records_used = cube.make.BMW.sellingprice.count
print(f"{records_total:,.0f} records in 'car_sales' dataset, \n"
      f"An individual query for each of the {len(makers):,.0f} car-makers ({', '.join(makers[:3])}...) will be executed '{address}'.\n"
      f"The query requests for the total 'sellingprice' of each each car-maker all of the {records_total:,.0f} records in total.\n"
      )

# **********************
duration = \
    timeit.Timer('x = [normal_read(make) for make in makers]', globals=globals()).repeat(repeat=loops, number=loops)[0]
print(f"{loops:,.0f}x read cube[{address}] caching 'NONE' in {duration:.3f} seconds, "
      f"{loops / duration * len(makers):,.0f} ops/sec, "
      f"{loops / duration * records_used * len(makers):,.0f} aggregations/sec, "
      f"{loops / duration * records_total * len(makers):,.0f} processed records/sec,")

duration = \
    timeit.Timer('y = [cached_read(make) for make in makers]', globals=globals()).repeat(repeat=loops, number=loops)[0]
print(f"{loops:,.0f}x read cube[{address}] caching '{caching_strategy}' in {duration:.3f} seconds, "
      f"{loops / duration * len(makers):,.0f} ops/sec, "
      f"{loops / duration * records_used * len(makers):,.0f} aggregations/sec, "
      f"{loops / duration * records_total * len(makers):,.0f} processed records/sec,")

duration = timeit.Timer('z = [df_read(make) for make in makers]', globals=globals()).repeat(repeat=loops, number=loops)[
    0]
print(
    f"{loops:,.0f}x direct read from dataframe by 'df.loc[df['make'] == 'BMW', 'sellingprice'].sum()' in {duration:.3f} seconds, "
    f"{loops / duration * len(makers):,.0f} ops/sec, "
    f"{loops / duration * records_used * len(makers):,.0f} aggregations/sec, "
    f"{loops / duration * records_total * len(makers):,.0f} processed records/sec,")

# **********************
maker = random.choice(makers)  # as an exmaple
print(f"\nreturned normal value for maker '{maker}'    := {normal_read(maker):,.0f}")
print(f"returned cached value for maker '{maker}'    := {cached_read(maker):,.0f}")
print(f"expected value (from df) for maker '{maker}' := {df_read(maker):,.0f}")

print("\nMemory footprint:")
collected = gc.collect()
print(f"\tdataframe  : {df.memory_usage(index=True).sum():,.0f} bytes")
