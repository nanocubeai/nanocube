import pandas as pd

from nanocube import cubed

df = pd.DataFrame({"product": ["Apple", "Pear", "Banana", "Apple", "Pear", "Banana"],
                   "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
                   "customer": ["Peter", "Peter", "Paul", "Paul", "Mary", "Mary"],
                   "sales": [100, 150, 300, 200, 250, 350],
                   "cost": [50, 90, 150, 100, 150, 175]})

cdf = cubed(df)

cdf.settings.debug_mode = True
context = cdf.product["Apple", "Pear"].sales
print(f"{context.address} = {context}")
