# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

import pandas as pd
from nanocube.datespan import parse, DateSpan
df = pd.DataFrame({"date": pd.date_range("2024-01-01", "2024-12-31")})

dss = parse("April 2024 ytd")# Create a DateSpanSet object
dss.add("May")               # Add a full month of the current year (e.g. 2024 in 2024)
dss.add("today")    # Add the current day from 00:00:00 to 23:59:59
dss += "previous week"       # Add a full week from Monday 00:00:00 to Sunday 23:59
dss -= "January"             # Remove the full month of January 2024

print(len(dss))              # returns the number of nonconsecutive DateSpans
print(dss.to_sql("date"))    # returns an SQL WHERE clause fragment
df = dss.filter(df, "date") # vectorized filtering of column 'date' of a DataFrame# )
print(df)                    # returns filtered DataFrame