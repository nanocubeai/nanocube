# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from nanocube import cubed

df = pd.DataFrame({"product": ["Apple", "Pear", "Banana", "Apple", "Pear", "Banana"],
                   "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
                   "customer": ["Peter", "Peter", "Paul", "Paul", "Mary", "Mary"],
                   "revenue": [100, 150, 300, 200, 250, 350],
                   "cost": [50, 90, 150, 100, 150, 175]})

cube = cubed(df)

# To return values from the cube, we need to "slice the cube" using the following syntax:
print(cube["*"])  # 1350
print(cube.Online)  # 550 = 100 + 150 + 300
print(cube.Online.Apple)  # 100
print(cube.Retail.Peter)  # 0
print(cube.Online.Apple.Peter)  # 100
print(cube.Online.Apple.cost)  # 50
