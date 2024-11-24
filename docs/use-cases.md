# Use Cases for CubedPandas

CubedPandas is a general purpose library to simplify and speed up data analysis with Pandas dataframes.
Here are some use cases and examples, where CubedPandas can be particularly useful and valuable.

## 1. Support for Novice Pandas Users
For novice users, CubedPandas can be a great help to get started with Pandas, as it hides some
of the complexity and verbosity of working with Pandas dataframes. Especially for business users
and citizen data analysts, who are not so familiar with Programming, CubedPandas can be much
less intimidating than using Pandas. Example

```python       
# Pandas - programming language
value = df.loc[(df['make'] == 'Audi') & (df['engine'] == 'hybrid'), 'price'].sum()
    
# CubedPandas - (more like) business language 
value = df.cubed.Audi.hybrid.price
```

## 2. Productivity Booster for Experienced Pandas Users
For experienced users, CubedPandas can be a great productivity booster, as it allows to write more compact,
readable and maintainable code. Some experts use it just to speed up their data filtering. Example:

```python       
# Let's assume you have a data file with a 'changed' column, 
# containing timestamps like '2024-06-18T12:34:56'.
# To get all records that 'changed' yesterday using  
# Pandas you would need to write something like this:
df = pd.read_csv('data.csv')
df['changed'] = pd.to_datetime(df['changed'])
df = df[df['changed'].dt.date == pd.Timestamp.now().date() - pd.Timedelta(days=1)]

# Using CubedPandas you can write:
df = pd.read_csv('data.csv').cubed.changed.yesterday.df    
# Note: Common English date phrases like today, yesterday, last_hour or lasthour, 
#       lastweek, lastmonth, last_year, next_month etc. will be resolved automatically.
```

## 3. Financial Data Analysis & Reporting

When it's all about the aggregation of financial and business data, CubedPandas really shines.
As multi-dimensional addresses are very close to our natural way of thinking, CubedPandas is
a perfect fit for reporting, business intelligence and even (minimal) data warehousing.

First, CubePandas provides direct and intuitive access to aggregated figures, e.g.:

```python
c = cubed(df)
trucks = c.region.North_America.sbu.Trucks.sales
delta_percent = (trucks.this_year - trucks.last_year) / trucks.last_year
if delta_percent > 0.1:
    # do something
    ...
```

Second, CubedPandas can be used to create reports and pivot-tables, e.g., you can easily
create a pivot table with the total sales per region and product:

```python
# Create a simple pivot table based on the above 'truck' filter with
# 'salesrep' and 'customer' in the rows and the last and 
# actual month sales in the columns. The 'sales' measure was already defined in trucks
trucks.slice(rows=c.salesrep & c.customer, columns=c.lastmonth & c.actualmonth)
```

CubedPandas automatically adds totals and sub-totals to the pivot table (not an easy task  
with Pandas alone) and also apply some basic formatting. More advanced pivot-table features
and also a set of standard data analysis can/will be added in the future, if there is demand
for such capabilities.

## 4. Data Quality Analysis
CubedPandas is also a great tool for data quality analysis. Due to the cell based data access, 
expected totals, missing values, duplicates, and other data quality issues can be easily checked.

```python
c = cubed(pd.read_csv('daily_delta.csv'))
any_nan_in_cube = c.NAN.any
missing_values_count = c.revenue.NAN.count
suspicious_records = c[c.revenue_ < c.profit_]    
```

!!! note
If you would like to share your own use case for CubedPandas, anonymously or with reference,
then please let me know, they'll be added here. Just leave me a comment in the
[CubedPandas GitHub discussions](https://github.com/Zeutschler/cubedpandas/discussions),
or by creating a [GitHub issue](https://github.com/Zeutschler/cubedpandas/issues).




