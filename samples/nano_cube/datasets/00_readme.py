import pandas as pd
from common import cubed

df = pd.DataFrame({"product":  ["Apple",  "Pear",   "Banana", "Apple",  "Pear",   "Banana"],
                   "channel":  ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
                   "customer": ["Peter",  "Peter",  "Paul",   "Paul",   "Mary",   "Mary"  ],
                   "mailing":  [True,     False,    True,     False,    True,     False   ],
                   "revenue":  [100,      150,      300,      200,      250,      350     ],
                   "cost":     [50,       90,       150,      100,      150,      175     ]})

df['profit'] = df['revenue'] - df['cost']

value = df.loc[(df["channel"] == "Online") & (df["product"] == "Apple"), "revenue"].sum()
print (value)  # 100

cdf = cubed(df)

value = cdf["Apple", "Online", "revenue"]

value = cdf.Apple.Online.revenue

cdf = cubed(df)  # That's it!




