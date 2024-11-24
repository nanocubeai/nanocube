# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

from datetime import datetime
import pandas as pd
from nanocube.datespan import DateSpanSet, DateSpan, parse

df = pd.DataFrame.from_dict({
    "product": ["A", "B", "C", "A", "B", "C"],
    "date": [datetime(2024, 6, 1), datetime(2024, 6, 2),
             datetime(2024, 7, 1), datetime(2024, 7, 2),
             datetime(2024, 12, 1), datetime(2023, 12, 2)],
    "sales": [100, 150, 300, 200, 250, 350]
})

# create a DateSpanSet
dss = DateSpanSet("June 2024")
print(dss)

# filter the DataFrame using the DateSpanSet
filtered = dss.filter(df, "date")
print("Filtered dataframe:")
print(filtered)

# filter a specific column/series using the DateSpanSet
filtered = dss.filter(df["date"])
print("\nFiltered series 'date':")
print(filtered)

mask = dss.filter(df["date"], return_mask=True)
print("\nMask for filter:")
print(mask)

print("\nIndexes of filtered rows:")
index = dss.filter(df["date"], return_index=True)
print(index)






