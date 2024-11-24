# (c) 2024 by Thomas Zeutschler, MIT License
import pandas as pd
from loguru import logger

from nanocube import NanoCube

logger.info("sample.")
# Create or load a DataFrame
# NOTE: `None` values in string columns are not supported,
# use a string placeholder like 'N/A' or '#NA' instead.
df = pd.DataFrame({'customer': ['A', 'B', 'A', 'B', 'A'],
                   'product':  ['P1', 'P2', 'P3', 'P1', 'P2'],
                   'promo':    [True, False, True, True, False],
                   'manager':  ['Ari', '#NA', 'Eve', 'Eve', 'Ari'],
                   'discount': [5, None, None, 20, 25],
                   'sales':    [100, 200, 300, 400, 500],
                   'cost':     [60, 90, 120, 200, 240]})

# Create a cube and query it
nc = NanoCube(df)
print(nc.get(customer='A', product='P1'))  # {'discount': 5.0, 'sales': 100, 'cost': 60}
print(nc.get(customer='A'))                # {'discount': 30.0, 'sales': 900, 'cost': 420}
print(nc.get(product=['P1', 'P2']))        # {'discount': 50.0, 'sales': 1200, 'cost': 590}
print(nc.get(promo=True))                  # {'discount': 25.0, 'sales': 800, 'cost': 380}
print(nc.get(manager='Ari'))               # {'discount': 30.0, 'sales': 600, 'cost': 300}
print(nc.get(manager='#NA'))               # {sales: 800, cost: 380}
print(nc.get('sales', promo=True))   # 800
print(nc.get('sales'))                     # 1500 all records
print(nc.get('sales', 'cost', customer='A'))  # [900, 420]
