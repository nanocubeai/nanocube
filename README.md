# NanoCube

## Lightning fast OLAP-style point queries on Pandas DataFrames.

![GitHub license](https://img.shields.io/github/license/Zeutschler/nanocube?color=A1C547)
![PyPI version](https://img.shields.io/pypi/v/nanocube?logo=pypi&logoColor=979DA4&color=A1C547)
![PyPI Downloads](https://img.shields.io/pypi/dm/nanocube.svg?logo=pypi&logoColor=979DA4&label=PyPI%20downloads&color=A1C547)
![GitHub last commit](https://img.shields.io/github/last-commit/Zeutschler/nanocube?logo=github&logoColor=979DA4&color=A1C547)
![unit tests](https://img.shields.io/github/actions/workflow/status/zeutschler/nanocube/python-package.yml?logo=GitHub&logoColor=979DA4&label=unit%20tests&color=A1C547)

-----------------

**NanoCube** is a super minimalistic, in-memory OLAP engine for lightning fast point queries
on Pandas DataFrames. It’s just 27 lines of code that magically transform any DataFrame into a 
multi-dimensional OLAP cube. NanoCube shines when many point queries are needed on the same DataFrame,
e.g. for financial data analysis, business intelligence or fast web services.

If you believe it would be valuable to **extend NanoCube with additional OLAP features** and improve its speed - 
_yes, that’s possible_ - please let me know. You can reach out by opening an issue or contacting me 
on [LinkedIn](https://www.linkedin.com/in/thomas-zeutschler/).

``` bash
pip install nanocube
```

```python
import pandas as pd
from nanocube import NanoCube

# create a DataFrame
df = pd.read_csv('sale_data.csv')
value = df.loc[(df['make'].isin(['Audi', 'BMW']) & (df['engine'] == 'hybrid')]['revenue'].sum().item()

# create a NanoCube and run sum aggregated point queries
cube = NanoCube(df)
for i in range(1000):
    value = cube.get('revenue', make=['Audi', 'BMW'], engine='hybrid')
```

### Lightning fast - really?
For aggregated point queries NanoCube are up to 100x or evn 1,000x times faster than Pandas. For the special purpose,
NanoCube is also much faster than all other libraries, like Spark, Polars, Modin, Dask or Vaex. If such 
libraries are drop-in replacements with Pandas dataframe, you should be able to accelerate them with NanoCube too.

As a rule of thump, using NanoCube is valuable for 10 or more point queries on a DataFrame, as the 
initialization time for 50k - 200k rows/sec the NanoCube needs to be taken consideration. 


### How is this possible?
NanoCube creates an in-memory multi-dimensional index over the entire dataframe using 
Roaring Bitmaps (https://roaringbitmap.org). This takes some time, but yields very fast filtering and point queries.

For each unique value in all dimension columns, a bitmap is created that represents the rows in the DataFrame 
where this value occurs. The bitmaps can then be combined or intersected to determine the rows relevant for 
a specific filter or point query. Once the relevant rows are determined, Numpy is used for aggregation of results. 

NanoCube is a by-product of the CubedPandas project (https://github.com/Zeutschler/cubedpandas) and will be integrated
into CubedPandas in the future. But for now, NanoCube is a standalone library that can be used with 
any Pandas DataFrame for the special purpose of point queries.

### What price do I have to pay?
First of all, no money. NanoCube is free and MIT licensed. But the first price you need to pay is 
some additional memory consumption, typically up to 25% on top of the original DataFrame size. 

The second price to pay, is the time needed to create the multidimensional index. The time is proportional 
to the size of the DataFrame (see below). 

Try may want to try and adapt the included sample [`sample.py`](sample.py) and benchmarks 
[`benchmark.py`](benchmark.py) and [`benchmark.ipynb`](benchmark.ipynb) to test the behavior of NanoCube 
on your data.

## NanoCube Benchmarks

Using the Python script [benchmark_ext.py](benchmark_ext.py), the following comparison charts can be created.
The data set contains 7 dimenion columns and 2 measure columns.

#### Point query for single row
A highly selective query, fully qualified and filtering on all 7 dimensions. The query will return and aggregates 1 single row.
NanoCube is 100x or more times faster than Pandas. 

![Point query for single row](charts/s.png)

#### Point query on high cardinality column
A highly selective, filtering on a single high cardinality dimension, where each member
represents ±0.01% of rows. NanoCube is 100x or more times faster than Pandas. 

![Query on single high cardinality column](charts/hk.png)


#### Point query aggregating 0.1% of rows
A highly selective, filtering on 1 dimension that affects and aggregates 0.1% of rows.
NanoCube is 100x or more times faster than Pandas. 

![Point query aggregating 0.1% of rows](charts/m.png)

#### Point query aggregating 5% of rows
A barely selective, filtering on 2 dimensions that affects and aggregates 5% of rows.
NanoCube is consistently 10x faster than Pandas. But you can already see, that the 
aggregation in Numpy become slightly more dominant. 

![Point query aggregating 5% of rows](charts/l.png)

#### Point query aggregating 50% of rows
A non-selective query, filtering on 1 dimension that affects and aggregates 50% of rows.
Here, most of the time is spent in Numpy, aggregating the rows. The more
rows, the closer Pandas and NanoCube get as both rely on Numpy for
aggregation.

![Point query aggregating 50% of rows](charts/xl.png)

#### NanoCube initialization time
The time required to initialize a NanoCube instance is linear.
Depending on the number of dimensions and the cardinality a throughput of
20k to 200k rows/sec can be expected. Almost all time is spent requesting
data from Pandas. The initialization of the Roaring Bitmaps taken no time.
Likely, a custom file format for NanoCube data would be highly beneficial.

![NanoCube initialization time](charts/init.png)



