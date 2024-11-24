# Getting started with CubedPandas

This guide will help you to get started with CubedPandas. It explains the concept and basic usage
and capabilities of CubedPandas.

[TOC]

## 1. Installation

CubedPandas is available via [PyPI.org](https://pypi.org/project/cubedpandas/) and can be
installed via pip. It is recommended to always use the latest version of CubedPandas, as CubedPandas is still under
constant development, new features are added frequently and know bugs get fixed.

```bash
pip install cubedpandas
```

## 2. The Basic Concept of Cubed Pandas

The main purpose of CubedPandas is to make working with Pandas easier and more intuitive, ideally also more fun.
As DataFrames are two-dimensional structures (tables), it is not always easy to access data in a way that is
close to our natural human way of thinking and analysing data. Therefore, CubedPandas introduces 2 main concepts:

### 2.1 Multi-Dimensional Cubes

CubedPandas borrows/mimics the concept of multi-dimensional cubes from OLAP (Online Analytical
Processing) databases and brings it to Pandas DataFrames. OLAP-style addressing of data is very close
to our natural way of thinking and data analysis, e.g. *Sales last year for trucks in North America.*
is a very natural way to ask for data.

CubedPandas **automatically infers a multi-dimensional schema** from your Pandas DataFrame which
then represents a **virtual multi-dimensional Cube** over the dataframe. By default, all numeric columns
of the DataFrame are considered as **Measures** - *the numeric values to analyse & aggregate* - all
other columns are considered as **Dimensions** - *to filter, navigate and view the data*.
The individual distinct values in a dimension column are called the **Members** of the dimension.

```python  linenums="1" hl_lines="14" title="Converting a Pandas DataFrame into a CubedPandas Cube"
import pandas as pd
from cubedpandas import cubed

# Create a Pandas dataframe with some sales data
df = pd.DataFrame(
    {"product":  ["Apple",  "Pear",   "Banana", "Apple",  "Pear",   "Banana"],
     "channel":  ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
     "customer": ["Peter",  "Peter",  "Paul",   "Paul",   "Mary",   "Mary"  ],
     "date":     ["2023/12/09","2024/04/16","2024/06/05","2024/06/27","2024/08/21","2024/09/07"],
     "mailing":  [True,     False,    True,     False,    True,     False   ],
     "sales":    [100,      150,      300,      200,      250,      350     ],
     "cost":     [50,       90,       150,      100,      150,      175     ]})

cdf = cubed(df)  # Turn your dataframe into a CubedPandas cube.
```

In the above example, `cdf` wraps the DataFrame into a 6-dimensional cube
with the following dimensions, individual members and measures

1. Dimension **product** with members *Apple, Pear, Banana*
2. Dimension **channel** with members *Online, Retail*
3. Dimension **customer** with members *Peter, Paul, Mary*
4. Dimension **date** with members *2023/12/09, 2024/04/16, 2024/06/05, 2024/06/27, 2024/08/21, 2024/09/07*
5. Dimension **mailing** with members *True, False*


1. Measure **revenue** with values *100, 150, 300, 200, 250, 350*
2. Measure **cost** with values *50, 90, 150, 100, 150, 175*

The basic idea of CubedPandas is to access **aggregated data** through **filtering the data by specific
dimension and members** for a specific measure of the cube. Example:

```python
assert(cdf.Apple.Online.sales == 100)
```

The previous statement will (try to) filter the DataFrame by `product = "Apple"`and `channel = "Online"`.
All records that match both conditions are then aggregated by the `sales` measure. As there is only one
record that matches both conditions, the result will be `100`. So the statement is identical to the following
Pandas and, for reference, SQL statements:

```python 
assert(df[(df["product"] == "Apple") & (df["channel"] == "Online")]["sales"].sum() == 100)
```

```SQL
SELECT SUM(sales) FROM df WHERE product = "Apple" AND channel = "Online" 
```

The default aggregation function is `sum`, but can be changed to any other aggregation function,
e.g. `mean`, `median`, `count`, `max`, `min`, `std`, `var` and others. For example:
`cdf.Apple.Online.sales.mean` will return the mean of all sales records that match the conditions
`product = "Apple"` and `channel = "Online"`.

### 2.2 Interact With Data To Minimize Distraction

The second main concept of CubedPandas is to make access to data as easy, intuitive and destruction free
as possible. To minimize syntax and coding CubedPandas introduces the concept of a **Context**. A context
references a single artefact or definition in the cube, e.g. a measure, a dimension, a measure, a filter etc.
Multiple contexts can then be combined or 'chained' to form a more complex context. In programming this concept
is well known and called *method chaining* or *fluent
interface* ([link](https://en.wikipedia.org/wiki/Fluent_interface)),
in CubedPandas we call this **"building a Context"**.

Whatever you will type, CubedPandas will try to resolve it into a context object. Let's assume you want to access:

```python
cdf = cubed(df)             # this method returns a Cube object
sales = cdf.Apple.sales     # this method returns a valid Context object
```

In the previous code fragment `cdf` is a CubedPandas `Cube` object instance and the root for all further
addressing and/or filtering using objects Context objects. Context objects can be defined/accessed in two ways:

#### 2.2.1 Using the `.` operator

By adding the `.` operator followed by a Python-compliant attribute name, e.g. `cdf.Apple` or `cdf.sales`.
As neither `Apple` nor `sales` are existing attributes/keywords of the Cube object, CubedPandas will try to
resolve them as measure, dimension or member names of the cube. If the resolution is successful, a new
Context object is created and returned. If the resolution fails, an error is raised. Further chaining
can be applied to create a subsequent context t, e.g. `cdf.Apple.sales` or `cdf.Apple.Online.sales`, there
is virtually no limitation in depth and length of chaining.

***Wait, wait, wait!*** What happens if a measure, dimension or member are not a Python-compliant attribute
names or even conflict with python keywords? E.g. `cdf.sales rep`, `cdf.True` or `cdf.2024/08/21` are reserved
or invalid Python attribute names. In this case you can use the `[]` operator as explained below or leverage the
various hacks that are build into CubedPandas to resolve such conflicts.

!!! caution
Please be aware that all **attribute names are case-sensitive**. Measure, dimension and member names must be
written exactly as they are contained in the DataFrame. You can use the `members` property of a dimension
context to get a list of all members of the dimension. But this also means that 'Apple' is not the same as
'apple' or 'APPLE'. For future releases of CubedPandas it is planned to provide a all-lower-case option to
resolve such case specific issues, typos and confusion.

A few examples of how some, not all, naming conflicts can be resolved:

```python
a = cdf.sales_rep  # use underscores to replace whitespaces "sales rep" := "sales_rep"
a = cdf.true       # use lower case for upper case Python Keywords like True or False 
a = cdf.And        # use upper case for lower case Python Keywords like and, or, not
```

#### 2.2.1 Using the `[...]` operator

The `[]` operator is the much more flexible and safe way to access and define Context objects.
It allows you to access measures, dimensions and members which arbitrary names, e.g. `cdf["sales rep"]`,
or any data type, e.g. `cdf[True]` or `cdf[datetime.now()]`. Whatever you throw into the `[]` operator,
CubedPandas will try to resolve it into a Context object. If the resolution fails, a (hopefully meaningful)
`ValueError` is raised so you can correct your code.

A few examples of how the `[]` operator can be used:

* `a = cdf.product["Apple"].sales`    
  This, using a `.` separated keyword for dimension and measure names and the `[]` operator for member names,
  is the most explicit, readable and fastest way to address/access/filter data.
  **It is recommended to use this form whenever possible!**
* `cdf.product["Apple"]`
  The keyword for the 'sales' measure can be omitted if yoiu want to access the default measure of the cube.
  By default, this is the first measure, from left to right, of the cube.
* `a = cdf["Apple"]`
  This is less explicit, and you might run into ambiguities if the same value is contained in multiple
  dimensions of the Cube. Also, as no dimension is specified, CubedPandas needs to investigate all dimensions
  to find the member `Apple`. For large DataFrames with high member cardinality, this can become slow.
* `cdf[True]`
  Here we are using a boolean value as a member of a dimension. CubedPandas will try to resolve it as a member
  from all dimensions of the cube that do or could contain boolean values. If the resolution is successful,
  a Context will be returned. So, this statement is identical to `cdf.mailing[True]` as mailing is the only
  dimension that contains boolean values.
* `cdf[datetime.now()]`
  Same example as the previous one, but now we are using a datetime object as a member of a dimension.
  CubedPandas will resolve the `date` dimension and try to find the member that matches the current date.
  So, this statement is identical to `cdf.date[datetime.now()]`.

## 3. The Basic Concepts of CubedPandas

In this chapter, we will present and explain all the basic concepts and conventions of CubedPandas.

### 3.1 Context = Data Cell = Numerical Value

When you build a context, e.g. `cdf.product.Apple.sales`, it always refers to a **single data cell** in
the multi-dimensional data space. Each cell represents a **single numerical value**, which is the aggregation
of all records in the DataFrame that match the conditions defined by the context. The default and most
used aggregation function is `sum`, therefore it can be omitted and the following 3 statements are identical:

```python
a = cdf.product.Apple.sales
b = cdf.product.Apple.sales.sum
c = cdf.product.Apple.sales.sum()
assert(a == b == c)
```

### 3.2 Aggregation Function Calls

Please note that the `()` operator in the sample above is optional to return a value from the context.
This due to fact that all aggregation functions are context objects by themselves. Using `()` to call the
method will terminate the context chain and return simple a numerical value, whereas omitting the `()` method
call will return a context object that can be further chained or used in other contexts.

```python
a = cdf.product.Apple.sales.sum     # returns a context object that can be further chained 
                                    # and behaves as a numerical value (float or int) at the same time
b = cdf.product.Apple.sales.sum()   # returns just a numerical value (float or int)

c = a.Online  # Will return the sales of Apple for the Online channel.
d = b.Online  # Will RAISE AN ERROR, as `b` is of type int or float.
```

### 3.3 Context Objects Behave Like Numerical Values

All context objects behave like numerical values, so you can use them in any numerical operation,
some examples:

```python   
a = cdf.product.Apple.sales
b = cdf.product.Pear.sales
avg_sales = (a + b) / cdf.product.Apple.Pear.count  # note: count returns the number of records
assert(avg_sales == cdf.product.Apple.Pear.sales.mean)
```

Please note that aggregation functions like `sum`, `max`, `min` return the same data type as from the
underlying DataFrame. Whereas `mean`, `median`, `std`, `var` return a float and `count`, `nunique` etc.
return an integer.

### 3.4 CubedPandas Data Types are Python Data Types

Other than Pandas, CubedPandas will always convert all data Pandas and Numpy specific datatypes
to the respective Python datatypes. This means, that all data types are either `int`, `float`, `str`, `bool`,
`datetime`, `date` or `time`. This makes it easier to work with the data in CubedPandas, as you don't
need to worry about the specific Pandas or Numpy data types.

### 3.5 Context Objects Are Lazy

CubedPandas evaluates the actual value of a context object only when it is needed. This means that
when you can build a multipart context object like `cdf.product.Apple.channel.Online.sales` then only
the filtering for each individual context object in the chain is evaluated. In addition, the filtering
is subsequently applied to the DataFrame, so the first context object in the chain needs to filter all
records of the DataFrame. The subsequent context objects in the chain then only need to filter the records
that are already filtered by the previous context objects.

!!! tip
If you filter on the most selective dimension first, you might be able to speed up the filtering
process quite a bit.

Evaluation of the actual value of a context object is only done when the context object is used in a numerical
operation or when used otherwise as a numerical value, e.g. for printing or showing the value while debugging.

### 3.6 Context Reuse Can Speed Up Your Code

If you need to access data from a certain area of the cube multiple times, it is recommended to store the
context object in a variable. This will prevent the re-evaluation of the context object and speed up your code.
The following code fragment shows how to iterate over all products that Peter bought Online.

```python
online_sales_with_peter = cdf.channel.Online.customer.Peter.sales
for member in online_sales_with_peter.product.members:
    print(f"Sales of {member} with Peter: {online_sales_with_peter[member]}")
```

### 3.7 Key Error Handling

By default, CubedPandas will raise a `KeyError` if a measure, dimension or member name can not be found in the
DataFrame. This is to help to detect typos and errors easily.

If you want to suppress ALL key errors, you can set the `ignore_key_errors` attribute to `True` either when you
create a `Cube` object, e.g. `cdf = cubed(df, ignore_key_errors=True)`, or through the `cube.settings`object.
Doing so, all requests against non-existing measure, dimension or member names will return `None` or `0`
instead of raising an error.

Wether `None` or `0` will be returned depends on the context, but mainly the value of the
`return_none_for_non_existing_cells` setting (default value is `False`) of the Cube object.
So be default, `0` will be returned for non-existing cells, but you can change this behaviour by setting
the attribute to `True`.

```python
cdf = cubed(df)             
fail = cdf.xyz123.sales     # This will RAISE AN ERROR as 'xyz123'   
                            # is not a valid measure, dimension or member name

cdf.settings.ignore_key_errors = True
no_fail = cdf.xyz123.sales  # This will return `0.0` as 'xyz123' does not exist in the DataFrame

cdf.settings.return_none_for_non_existing_cells = True
no_fail = cdf.xyz123.sales  # Now it will return `None` 
```

If you want to suppress key errors for members only, you can set the `ignore_member_key_errors` attribute to `True`.
This will suppress key errors for member names only, but not for measure or dimension names. This approach is
recommended if you want check for specific members in a dimension, but you are unsure if the exist and don't want to
raise an error if the member does not exist.

```python
cdf = cubed(df)
fail = cdf.product.xyz123.sales     # This will RAISE AN ERROR as 'xyz123'   
                                    # is not a valid member name of the 'product' dimension
                                    
cdf.settings.ignore_member_key_errors = True
no_fail = cdf.product.xyz123.sales  # This will return `0.0` as 'xyz123' is not contained in the 'product' dimension
fail = cdf.xyz123.sales             # This will RAISE AN ERROR as 'xyz123' 
                                    # is not a valid measure, dimension or member name
```

For a future version of CubedPandas, it is planned to add individual behaviours for key-errors per dimension into
the schema. This will allow you to define if key errors should be ignored for a specific dimension or not.

### 3.8 Boolean Dimensions

If a dimension contains boolean values only (the underlying Pandas DataFrame column is of type `bool`),
CubedPandas will try resolve either the boolean value `True` or `False` as the requested member of the dimension.

CubedPandas supports various aliases for `True` and `False`, e.g. `yes` and `no`, `on` and `off`, `1` and `0`.
The following statements are all identical:

```python
cdf = cubed(df)
mailing = cdf.mailing[True].sales
mailing = cdf.mailing["TruE"].sales
mailing = cdf.mailing["Yes"].sales
mailing = cdf.mailing["on"].sales
mailing = cdf.mailing[1].sales
```

As boolean dimensions are quite common in data analysis, CubedPandas assumes that when you use the dimension name
only, you are referring to the `True` member of the dimension. So, `cdf.mailing.sales` is identical to
`cdf.mailing[True].sales` and the `[True]` argument can be omitted.











