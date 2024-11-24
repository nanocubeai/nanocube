# Question what is the fastest way to generate a roaring bitmap index from a vector of values?
from datetime import datetime

import pandas as pd
import numpy as np
import pyroaring
from pyroaring import BitMap
import pyarrow as pa


# current approach, eating what comes first
def collect_bitmaps(df, dimensions):
    dimensions: dict = dict([(col, i) for i, col in enumerate(dimensions)])
    bitmaps: list = []  # bitmaps per dimension per member containing the row ids of the DataFrame
    for dimension in dimensions.keys():
        member_bitmaps = {}
        for row, member in enumerate(df[dimension].to_numpy()):
            if member not in member_bitmaps:
                member_bitmaps[member] = BitMap([row])
            else:
                member_bitmaps[member].add(row)
        bitmaps.append(member_bitmaps)

# list based approach, as fast as the current approach but
def collect_bitmaps_list(df, dimensions):
    dimensions: dict = dict([(col, i) for i, col in enumerate(dimensions)])
    bitmaps: list = []  # bitmaps per dimension per member containing the row ids of the DataFrame
    for dimension in dimensions.keys():
        member_bitmaps = {}
        for row, member in enumerate(df[dimension].to_list()):
            if member not in member_bitmaps:
                member_bitmaps[member] = [row,]
            else:
                member_bitmaps[member].append(row)
        for member in member_bitmaps.keys():
            bitmap = BitMap()
            bitmap.update(member_bitmaps[member])
            member_bitmaps[member] = bitmap
        bitmaps.append(member_bitmaps)

# numpy sorted approach
def collect_bitmaps_numpy(df, dimensions):
    dimensions: dict = dict([(col, i) for i, col in enumerate(dimensions)])
    bitmaps: list = []  # bitmaps per dimension per member containing the row ids of the DataFrame
    rows_count = len(df.index)
    for dimension in dimensions.keys():
        member_bitmaps = {}
        rows = df[dimension].to_numpy()

        # replace nan values with a string
        rows = np.where((rows == None) | (rows.astype(str) == 'nan'), "", rows)

        idx = np.argsort(rows, kind='stable')
        sorted = rows[idx].tolist()

        value = sorted[0]
        start = 0
        for i in range(1, rows_count):
            if sorted[i] != value:
                # next value, get list of all indexes of the previous value
                # from start to i and add to a new bitmap.
                bitmap = BitMap()
                member_bitmaps[value] = bitmap.update(idx[start:i])
                value = sorted[i]
                start = i
        # add the last bitmap
        bitmap = BitMap()
        member_bitmaps[value] = bitmap.update(idx[start:rows_count])
        bitmaps.append(member_bitmaps)


if __name__ == '__main__':

    # Use the care sales dataset for testing
    file_car_prices = "files/car_prices.parquet"
    df = pd.read_parquet(file_car_prices)
    dimensions = ['make', 'model', 'trim', 'body']

    start = datetime.now()
    collect_bitmaps(df, dimensions)
    duration = datetime.now() - start
    print(f"Current approach: {duration.total_seconds()} sec.")

    start = datetime.now()
    collect_bitmaps_list(df, dimensions)
    duration = datetime.now() - start
    print(f"List sorted approach: {duration.total_seconds()} sec.")


    start = datetime.now()
    collect_bitmaps_numpy(df, dimensions)
    duration = datetime.now() - start
    print(f"Numpy sorted approach: {duration.total_seconds()} sec.")

