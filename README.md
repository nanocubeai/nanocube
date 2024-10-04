# NanoCube

## Lightning fast OLAP-style point queries on Pandas DataFrames.

![GitHub license](https://img.shields.io/github/license/Zeutschler/nanocube?color=A1C547)
![PyPI version](https://img.shields.io/pypi/v/nanocube?logo=pypi&logoColor=979DA4&color=A1C547)
![PyPI Downloads](https://img.shields.io/pypi/dm/nanocube.svg?logo=pypi&logoColor=979DA4&label=PyPI%20downloads&color=A1C547)
![GitHub last commit](https://img.shields.io/github/last-commit/Zeutschler/nanocube?logo=github&logoColor=979DA4&color=A1C547)
![unit tests](https://img.shields.io/github/actions/workflow/status/zeutschler/nanocube/python-package.yml?logo=GitHub&logoColor=979DA4&label=unit%20tests&color=A1C547)

-----------------

**NanoCube** is a super minimalistic, in-memory OLAP cube implementation for lightning fast point queries
upon Pandas DataFrames. It consists of only 27 lines of magical code that turns any DataFrame into a 
multi-dimensional OLAP cube. NanoCube shines when multiple point queries are needed on the same DataFrame,
e.g. for financial data analysis, business intelligence or fast web services.

``` bash
pip install nanocube
```

```python
import pandas as pd
from nanocube import Cube

# create a DataFrame
df = pd.read_csv('sale_data.csv')
value = df.loc[(df['make'].isin(['Audi', 'BMW']) & (df['engine'] == 'hybrid')]['revenue'].sum().item()

# create a NanoCube and run sum aggregated point queries
cube = Cube(df)
for i in range(1000):
    value = cube.get('revenue', make=['Audi', 'BMW'], engine='hybrid')
```

### Lightning fast - really?
For aggregated point queries NanoCube is 100x to 1,000x times faster than Pandas. For the special purpose,
NanoCube is also much faster than all other libraries, like Spark, Polars, Modin, Dask or Vaex. If such 
libraries are drop-in replacements with Pandas dataframe, you should be able to use them with NanoCube too. 

### How is this possible?
NanoCube uses a different approach. Roaring Bitmaps (https://roaringbitmap.org) are used to construct 
a multi-dimensional in-memory presentation of a DataFrame. For each unique value in a column, a bitmap is created
that represents the rows in the DataFrame where this value occurs. The bitmaps are then combined to identify the 
rows relevant for a specific point query. Numpy is finally used for aggregation of results. 
NanoCube is a by-product of the CubedPandas project (https://github.com/Zeutschler/cubedpandas) and the result
of the attempt to make OLAP-style queries on Pandas DataFrames as fast as possible in a minimalistic way.

### What price do I need to pay?
First of all, NanoCube is free and MIT licensed. The first price you need to pay is the memory consumption, typically
up to 25% on top of the original DataFrame size. The second price is the time needed to initialize the cube, which is
mainly proportional to the number of unique values over all dimension columns in the DataFrame. Try the included samples
`sample.py` or notebook to get a feeling for the performance of NanoCube.






(100x to 1000x times faster than Pandas). By default, all non-numeric columns will be
used as dimensions and all numeric columns as measures. Roaring Bitmaps (https://roaringbitmap.org) are used
to construct and query a multi-dimensional cube, Numpy is used for aggregations.