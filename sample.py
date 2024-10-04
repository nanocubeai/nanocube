# (c) 2024 by Thomas Zeutschler, MIT License
import pandas as pd
from nanocube import Cube

# Create or load a DataFrame
df = pd.DataFrame({'customer': [ 'A',  'B',  'A',  'B',  'A'],
                   'product':  ['P1', 'P2', 'P3', 'P1', 'P2'],
                   'promo':    [True, False, True, True, False],
                   'sales':    [ 100,  200,  300,  400,  500],
                   'cost':     [  60,   90,  120,  200,  240]})

# Create a cube and query it
cube = Cube(df)
print(cube.get(customer='A', product='P1'))  # {sales: 100, cost: 60}
print(cube.get(customer='A'))                # {sales: 900, cost: 420}
print(cube.get(product=['P1', 'P2']))        # {sales: 1200, cost: 590}
print(cube.get(promo=True))                  # {sales: 800, cost: 380}
print(cube.get('sales', promo=True))   # 800
print(cube.get('sales'))                     # 1500 all records
print(cube.get('sales', 'cost', customer='A')) # [900, 420]
