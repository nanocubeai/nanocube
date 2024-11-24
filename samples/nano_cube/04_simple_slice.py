# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
from datetime import datetime

import pandas as pd
from nanocube import cubed


df = pd.DataFrame({"product": ["Apple", "Pear", "Banana", "Apple", "Pear", "Banana"],
                   "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
                   "customer": ["Peter", "Peter", "Paul", "Paul", "Mary", "Mary"],
                   "revenue": [100, 150, 300, 200, 250, 350],
                   "cost": [50, 90, 150, 100, 150, 175]})
cdf = cubed(df)

# defined slice
slice = cdf.slice(rows=[dim for dim in cdf.schema.dimensions], columns=cdf.schema.measures)
print(slice)

slice = cdf.Online.slice(rows=cdf.schema.dimensions, columns=cdf.schema.measures)
print(slice)
