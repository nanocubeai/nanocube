from pandas import read_csv as pd_read_csv
from nanocube import NanoCube
from polars import read_csv, col

def filter_with_polars():
    df = read_csv("files/spotify_data.csv")
    result = df.filter(col("Daily") == 1337404).select("Streams").sum()
    print(result)
    # shape: (1, 1)
    # ┌────────────┐
    # │ streams    │
    # │ ---        │
    # │ i64        │
    # ╞════════════╡
    # │ 3518744128 │
    # └────────────┘

def filter_with_nanocube():
    df = pd_read_csv("files/spotify_data.csv")
    # FIXME: issue #7 -> solved: Daily was used a measure by default, querying it as a dimension will return all rows.
    # nc = NanoCube(df)
    nc = NanoCube(df, dimensions=['Daily'], measures=['Streams'])
    result = nc.get("Streams", Daily=1337404)
    print(result)
    # 2345359210015

def filter_with_pandas():
    df = pd_read_csv("files/spotify_data.csv")
    result = df.loc[(df['Daily'] == 1337404)]['Streams'].sum()
    print(result)
    # 2345359210015

if __name__ == "__main__":
    filter_with_polars()
    filter_with_nanocube()
    filter_with_pandas()
    # main()