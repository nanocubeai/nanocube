from pyspark.sql.group import dfapi

## Date & Time Intelligence (Under Construction)

Analysing data often requires the ability to filter or compare data over time. That can become quite tricky with
plain Pandas. CubedPandas offers a constantly growing set of **date & time intelligence functions**,
that will help you to filter, aggregate and compare your data over time like a pro. Just to give you an idea:

```Python
c = cubed(df)  # Turn your DataFrame into a CubedPandas cube
a = c.sales.oder_date.last_month
b = c.sales.oder_date["last 3 month on Mondays"].avg()
```

Most of the date & time intelligence functions like `last_month` will be resolved
relative to the actual datetime `= datetime.now()` and will return a from-to-date-range represented by
a tuple of two Python datetime objects. Example:

```Python
# this Pandas code
a = df[(df["order_date"].between(datetime(2024, 1, 1), datetime(2024, 1, 31)), "sales")].sum()
# can be written as this
a = c.sales.oder_date.jan_2024  # 'jan_2024' resolved to (datetime(2024, 1, 1), datetime(2024, 1, 31))
```

### Sample Dataset

To explain all the date and time intelligence functions, we will use the follwoing sample dataset.
It contains two date columns, `order_date `and `delivery_date`, some measure columns like `sales`
that can be aggregated and a couple of other columns, like `product`.

| product | ... | order_date | delivery_date | sales | cogs |
|---------|-----|------------|---------------|-------|------|
| A       | ... | 2021-01-01 | 2021-01-14    | 100   | 50   |
| F       | ... | 2021-01-02 | 2021-01-06    | 100   | 60   |
| ...     | ... | ...        | ...           | ...   | ...  |
| D       | ... | 2024-08-14 | 2024-09-03    | 200   | 110  |
| X       | ... | 2024-08-16 | NaN           | 300   | 150  |

## Simple Date & Time Intelligence

The date and time intelligence functions in CubedPandas are designed to be as simple and forgiving as possible.
As of now, they can be written in plain English using with spaces or underscores and can be accessed as Context
attributes or through the index `[]` operator.

```Python
c = cubed(df)  # Turn your DataFrame into a CubedPandas cube
a = c.sales.oder_date.last_month  # context attribute
b = c.sales.oder_date["last month"]  # context index [] operator
``` 

## Simple Date Related Phrases Functions

The following date related functions are available for date columns/dimension in a CubedPandas cube:

### Day Related Functions

| Function                       | Description                                                |
|--------------------------------|------------------------------------------------------------|
| `today`                        | The entire current day from time 00:00:00 to 23:59:59:999  |
| `yesterday`                    | The entire previous day from time 00:00:00 to 23:59:59:999 |
| `prev_day`, `prev day`         | same as `yesterday`                                        |                                   
| `previous_day`, `previous day` | same as `yesterday`                                        |                                  
| `tomorrow`                     | The entire next day from time 00:00:00 to 23:59:59:999     |     

### Week Related Functions

| Function                         | Description                                                         |
|----------------------------------|---------------------------------------------------------------------|
| `this_week`, `this week`         | The entire current week from Monday 00:00:00 to Sunday 23:59:59:999 | 
| `last_week`, `last week`         | The entire last week from Monday 00:00:00 to Sunday 23:59:59:999    |
| `prev_week`, `prev week`,        | same as `last_week`                                                 |                                                   | 
| `previous_week`, `previous week` | same as `last_week`                                                 |                                                   |
| `next_week`, `next week`         | The entire next week from Monday 00:00:00 to Sunday 23:59:59:999    |    

### Month Related Functions

| Function                           | Description                                                         |
|------------------------------------|---------------------------------------------------------------------|
| `this_month`, `this month`         | The entire current month from 1st 00:00:00 to last day 23:59:59:999 |
| `last_month`, `last month`         | The entire last month from 1st 00:00:00 to last day 23:59:59:999    |
| `prev_month`, `prev month`,        | same as `last_month`                                                |
| `previous_month`, `previous month` | same as `last_month`                                                |
| `next_month`, `next month`         | The entire next month from 1st 00:00:00 to last day 23:59:59:999    |

### Year Related Functions

| Function                         | Description                                                            |
|----------------------------------|------------------------------------------------------------------------|
| `this_year`, `this year`         | The entire current year from 1st Jan 00:00:00 to 31st Dec 23:59:59:999 |
| `last_year`, `last year`         | The entire last year from 1st Jan 00:00:00 to 31st Dec 23:59:59:999    |
| `prev_year`, `prev year`,        | same as `last_year`                                                    |
| `previous_year`, `previous year` | same as `last_year`                                                    |
| `next_year`, `next year`         | The entire next year from 1st Jan 00:00:00 to 31st Dec 23:59:59:999    |

## Simple Time Related Phrases Functions

The following Time related functions are available for date columns/dimension in a CubedPandas cube:

### Hour Related Functions

| Function                         | Description                                                |
|----------------------------------|------------------------------------------------------------|
| `this_hour`, `this hour`         | The entire current hour from time 00:00:00 to 59:59:59:999 |
| `last_hour`, `last hour`         | The entire last hour from time 00:00:00 to 59:59:59:999    |
| `prev_hour`, `prev hour`         | same as `last_hour`                                        |
| `previous_hour`, `previous hour` | same as `last_hour`                                        |
| `next_hour`, `next hour`         | The entire next hour from time 00:00:00 to 59:59:59:999    |

### Minute Related Functions

| Function                             | Description                                                  |
|--------------------------------------|--------------------------------------------------------------|
| `this_minute`, `this minute`         | The entire current minute from time 00:00:00 to 59:59:59:999 |
| `last_minute`, `last minute`         | The entire last minute from time 00:00:00 to 59:59:59:999    |
| `prev_minute`, `prev minute`         | same as `last_minute`                                        |
| `previous_minute`, `previous minute` | same as `last_minute`                                        |
| `next_minute`, `next minute`         | The entire next minute from time 00:00:00 to 59:59:59:999    |

### Second Related Functions

| Function                             | Description                                                  |
|--------------------------------------|--------------------------------------------------------------|
| `this_second`, `this second`         | The entire current second from time 00:00:00 to 59:59:59:999 |
| `last_second`, `last second`         | The entire last second from time 00:00:00 to 59:59:59:999    |
| `prev_second`, `prev second`         | same as `last_second`                                        |
| `previous_second`, `previous second` | same as `last_second`                                        |
| `next_second`, `next second`         | The entire next second from time 00:00:00 to 59:59:59:999    |

## Postfixes

The following postfixes can be used to further specify the date and time intelligence functions:

### Day Postfixes

| Postfix | Description                                                                                   |
|---------|-----------------------------------------------------------------------------------------------|
| `on`    | The entire day of the week, e.g. `on Monday`, `on Tuesday`, ...                               |
| `to`    | The entire day range, e.g. `last Monday to last Friday`, `next Tuesday to next Saturday`, ... |
| `of`    | The entire day of the month, e.g. `of January`, `of February`, ...                            |

### Week Postfixes

| Postfix | Description                                                          |
|---------|----------------------------------------------------------------------|
| `on`    | The entire week of the month, e.g. `on 1st week`, `on 2nd week`, ... |

The following functions are available for date columns/dimension in a CubedPandas cube:

| Function | Description                                                                             |
|----------|-----------------------------------------------------------------------------------------|
| `ytd`    | Year to date, the entire year from 1st Jan to today                                     |
| `qtd`    | Quarter to date, the entire quarter from 1st Jan, Apr, Jul, Oct to today                |
| `mtd`    | Month to date, the entire month from 1st to today                                       |
| `wtd`    | Week to date, the entire week from Monday to today                                      |
| `yoy`    | Year over year, the entire year from 1st Jan last year to today                         |
| `qoq`    | Quarter over quarter, the entire quarter from 1st Jan, Apr, Jul, Oct last year to today |
| `mom`    | Month over month, the entire month from 1st last month to today                         |
| `wow`    | Week over week, the entire week from Monday last week to today                          |


