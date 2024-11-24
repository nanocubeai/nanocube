class Bar:
    @property
    def baz(self) -> int:
        return 1

class Foo:
    def __getattr__(self, name) -> Bar:
        return Bar()

f = Foo()
b = Bar()
assert (type(f.bar) == type(Bar()))
assert (type(f.xyz) == type(Bar()))


# Type hint for non-existing attribute `f.bar` shows the `baz` attribute 👍
print(f.bar)

# ...but for non-existing attribute `f.xyz` it doesn't 👎. Bug or feature?
print(f.xyz)


import pandas as pd

df = pd.read_parquet("datasets/car_prices.parquet")
df.to_csv("datasets/car_prices.csv", index=False)

