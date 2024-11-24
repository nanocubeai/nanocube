# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
import pandas as pd
from nanocube import cubed

# Load the sample dataset
cdf = cubed(pd.read_csv('web_app/data.csv'))
slice = cdf.slice((cdf.Product_line, cdf.Gender, cdf.City), max_rows=100)
print(slice)
