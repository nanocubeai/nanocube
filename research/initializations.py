# importing libraries
import pandas as pd
from nanocube import NanoCube

# Create a DataFrame and NanoCube
file_car_prices = "files/car_prices.parquet"
df = pd.read_parquet(file_car_prices) #.head(100_000)
nc = NanoCube(df,
              dimensions=['year', 'make', 'model', 'trim', 'body',],  # 'transmission', 'vin', 'state', 'condition', 'color', 'interior', 'seller', 'saledate'],
              measures=['odometer', 'mmr', 'sellingprice'])
nc.save('files/car_prices.nano')
print(df.shape)
