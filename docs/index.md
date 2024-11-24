# CubedPandas Documentation

Welcome to the CubedPandas Documentation site. Here you will find all the information you need to get 
started with CubedPandas, a powerful and easy-to-use Python library for working with Pandas dataframes.

!!! note
    CubedPandas is in an early stage of development, your 
    [Ideas, Issues](https://github.com/Zeutschler/cubedpandas/issues) and 
    [Feedback](https://github.com/Zeutschler/cubedpandas/discussions) 
    are very welcome to make CubedPandas even more awesome. Many thanks!

## OLAP comfort meets Pandas power!
 
CubedPandas offer a new ***easy, fast & fun approach to navigate and analyze Pandas dataframes***.
CubedPandas is inspired by the powerful concepts of OLAP (Online Analytical Processing) and MDX (Multi-Dimensional
Expressions) and aims to bring the comfort and power of OLAP to Pandas dataframes.

For novice users, CubedPandas can be a great help to get started with Pandas, as it hides some
of the complexity and verbosity of Pandas dataframes. For experienced users, CubedPandas
can be a productivity booster, as it allows you to write more compact, readable and
maintainable code. Just to give you a first idea, this Pandas code

```python
# Pandas: calculate the total revenue of all hybrid Audi cars
value = df.loc[(df['make'] == 'Audi') & (df['engine'] == 'hybrid'), 'price'].sum()
```

turns into this CubedPandas code

```python
# CubedPandas: calculate the total revenue of all hybrid Audi cars
value = df.cubed.Audi.hybrid.price
```

As CubedPandas does not duplicate data or modifies the underlying dataframe and does not add
any performance penalty - in some cases can even boost Pandas performance by factors - it can be
used in production without any concerns and should be of great help in many use cases.

In [Jupyter notebooks](https://jupyter.org), CubedPandas will really start to shine. For further
information, please visit the [CubedPandas Documentation](https://zeutschler.github.io/cubedpandas/)
or try the included samples.

### Getting Started

CubedPandas is available on pypi.org (https://pypi.org/project/cubedpandas/) and can be installed by

```console
pip install cubedpandas
```

Using CubedPandas is as simple as wrapping any Pandas dataframe into a cube like this:

```python
import pandas as pd
from cubedpandas import cubed

# Create a dataframe with some sales data
df = pd.DataFrame({"product":  ["Apple",  "Pear",   "Banana", "Apple",  "Pear",   "Banana"],
                   "channel":  ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
                   "customer": ["Peter",  "Peter",  "Paul",   "Paul",   "Mary",   "Mary"  ],
                   "mailing":  [True,     False,    True,     False,    True,     False   ],
                   "revenue":  [100,      150,      300,      200,      250,      350     ],
                   "cost":     [50,       90,       150,      100,      150,      175     ]})

cdf = cubed(df)  # Wrapp your dataframe into a cube and start using it!
```

CubedPandas **automatically infers a multi-dimensional schema** from your Pandas dataframe which 
defines a virtual **Cube** over the dataframe. By default, numeric columns of the dataframe 
are considered as **Measures** - *the numeric values to analyse & aggregate* - all other columns are 
considered as **Dimensions** - *to filter, navigate and view the data*. The individual values in a 
dimension column are called the **Members** of the dimension. In the example above, column `channel`
becomes a dimension with the two members `Online` and `Retail`, `revenue` and `cost` are our measures.

Although rarely required, you can also define your own schema. Schemas are quite powerful and flexible, 
as they will allow you to define dimensions and measures, aliases and (planned for upcoming releases)
also custom aggregations, business logic, number formating, linked cubes (star-schemas) and much more.

### Context please, so I will give you data!
One key feature of CubePandas is an easy & intuitive access to individual **Data Cells** in
multi-dimensional data space. To do so, you'll need to define a multi-dimensional **Context** so
CubedPandas will evaluate, aggregate (`sum` by default) and return the requested value from 
the underlying dataframe.

**Context objects behave like normal numbers** (float, int), so you can use them directly in arithmetic
operations. In the following examples, all addresses will refer to the exactly same rows from the dataframe
and thereby all return the same value of `100`. 

```python
# Let Pandas set the scene...
a = df.loc[(df["product"] == "Apple") & (df["channel"] == "Online") & (df["customer"] == "Peter"), "revenue"].sum()

# Can we do better with CubedPandas? 
b = cdf["product:Apple", "channel:Online", "customer:Peter"].revenue  # explicit, readable, flexible and fast  
c = cdf.product["Apple"].channel["Online"].customer[
    "Peter"].revenue  # ...better, if column names are Python-compliant  
d = cdf.product.Apple.channel.Online.customer.Peter.revenue  # ...even better, if member names are Python-compliant

# If there are no ambiguities in your dataframe - what can be easily checked - then you can use this shorthand forms:
e = cdf["Online", "Apple", "Peter", "revenue"]
f = cdf.Online.Apple.Peter.revenue
g = cdf.Online.Apple.Peter  # as 'revenue' is the default (first) measure of the cube, it can be omitted

assert a == b == c == d == e == f == g == 100
```

Context objects also act as **filters on the underlying dataframe**. So you can use also CubedPandas for
fast and easy filtering only, e.g. like this:

```python   
df = df.cubed.product["Apple"].channel["Online"].df
df = df.cubed.Apple.Online.df  # short form, if column names are Python-compliant and there are no ambiguities
```

### Pivot, Drill-Down, Slice & Dice

The Pandas pivot table is a very powerful tool. Unfortunately, it is quite verbose and very hard to master.
CubedPandas offers the `slice` method to create pivot tables in a more intuitive and easy way, e.g. by default

```python   
# Let's create a simple pivot table with the revenue for dimensions products and channels
cdf.slice(rows="product", columns="channel", measures="revenue")
```

For further information, samples and a complete feature list as well as valuable tips and tricks,
please visit the [CubedPandas Documentation](https://zeutschler.github.io/cubedpandas/).


### Your feedback, ideas and support are very welcome!
Please help improve and extend CubedPandas with **your feedback & ideas** and use the 
[CubedPandas GitHub Issues](https://github.com/Zeutschler/cubedpandas/issues) to request new features and report bugs. 
For general questions, discussions and feedback, please use the 
[CubedPandas GitHub Discussions](https://github.com/Zeutschler/cubedpandas/discussions).

If you have fallen in love with CubedPandas or find it otherwise valuable, 
please consider to [become a sponsor of the CubedPandas project](https://github.com/sponsors/Zeutschler) so we 
can push the project forward faster and make CubePandas even more awesome.


*...happy cubing!*
