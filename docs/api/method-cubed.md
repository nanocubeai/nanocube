# Wrapping a Pandas DataFrame into a CubedPandas Cube

##  Using the 'cubed()' Method

The `cubed` function is the most convenient way to wrap and convert a Pandas dataframe into a CubedPandas cube.
by the way, `cdf` is nice and short for a 'cubed data frame' following the Pandas convention of `df` for a 'data frame'.

If no schema is provided when applying the `cubed` method, a schema will be automatically inferred from the DataFrame. 
By default, all numeric columns will be considered as measures, all other columns as dimensions of the cube.

```python
import pandas as pd
from cubedpandas import cubed

df = pd.DataFrame({"channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
                   "product": ["Apple",  "Pear",   "Banana", "Apple",  "Pear",   "Banana"],
                   "sales":   [100,      150,      300,      200,      250,      350     ],})
cdf = cubed(df)    
print(cdf.Online)  # returns 550 = 100 + 150 + 300
```

Sometimes, e.g. if you want an `integer` column to be considered as a dimension not as a measure column, 
you need to provide a schema. Here's a simple example of how to define and use a schema, here identical 
to schema that will be automatically inferred. For more information please refer to the 
[Schema](class-schema.md) documentation.

```python
import pandas as pd
from cubedpandas import cubed

df = pd.DataFrame({"channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
                   "product": ["Apple",  "Pear",   "Banana", "Apple",  "Pear",   "Banana"],
                   "sales":   [100,      150,      300,      200,      250,      350     ],})
schema = {"dimensions": [{"column":"channel"}, {"column": "product"}],
          "measures":   [{"column":"sales"}]}
cdf = cubed(df, schema=schema)
print(cdf.Online)  # returns 550 = 100 + 150 + 300
```

##  Using the 'cubed' extension for Python

After CubedPandas has been loaded, e.g. by `import cubedpandas`, you can also directly use the `cubed` extension
for Pandas. The only difference to the `cubed()` function is, that you need to use the `cubed` attribute of the
Pandas DataFrame and either slice it with the `[]` operator or get access to the cube or any context 
using the `.` operator.  

```python
import pandas as pd
import cubedpandas

df = pd.DataFrame({"channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
                   "product": ["Apple",  "Pear",   "Banana", "Apple",  "Pear",   "Banana"],
                   "sales":   [100,      150,      300,      200,      250,      350     ],})
                   
cdf = df.cubed.cube  # return a reference to the cube, just 'df.cubed' will not work.
# or directly access any context the cube either by slicing with the [] operator
x = df.cubed["Online", "Apple", "sales"]
# or by using the . operator
y = df.cubed.Online.Apple.sales

assert(x == y == 100)
```

::: cubedpandas.common
    options:
      members:
      - cubed




::: cubedpandas.pandas_extension
    options:
      members:
      - CubedPandasAccessor

