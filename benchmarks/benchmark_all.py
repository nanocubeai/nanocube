# nanocube - Copyright (c)2024, Thomas Zeutschler, MIT license
import random
import string
import datetime
import matplotlib.pyplot as plt
from matplotlib import ticker
import pandas as pd
import polars as pl
from nanocube import NanoCube as NanoCube
import sqlite3
import pyarrow as pa
import pyarrow.compute as pc

# 1. declare global variables
df: pd.DataFrame  | None = None
nc_r: NanoCube | None = None
nc_n: NanoCube | None = None
pl_df: pl.DataFrame | None = None
pat: pa.Table | None = None
sqlite: sqlite3.Connection | None = None
sqlite_cursor: sqlite3.Connection | None = None

sqlite_idx: sqlite3.Connection | None = None
sqlite_idx_cursor: sqlite3.Connection | None = None

# 2. data loading methods
def load_pandas(data: pd.DataFrame):
    global df
    df = data

def load_nanocube_roaring(data: pd.DataFrame):
    global nc_r
    dimensions = ['promo', 'segment', 'customer', 'category', 'date', 'product', 'orderid']
    measures = ['sales', 'cost']
    nc_r = NanoCube(data, dimensions=dimensions, measures=measures, caching=False, indexing_method='roaring')

def load_nanocube_numpy(data: pd.DataFrame):
    global nc_n
    dimensions = ['promo', 'segment', 'customer', 'category', 'date', 'product', 'orderid']
    measures = ['sales', 'cost']
    nc_n = NanoCube(data, dimensions=dimensions, measures=measures, caching=False, indexing_method='numpy')

def load_polars(data: pd.DataFrame):
    global pl_df
    pl_df = pl.from_pandas(data)

def load_arrow(data: pd.DataFrame):
    global pat
    pat = pa.Table.from_pandas(data)

def load_duckdb(data: pd.DataFrame):
    source_df: pd.DataFrame = data
    duckdb.connect(':memory:')
    duckdb.sql(f"DROP TABLE IF EXISTS car_prices")
    duckdb.sql(f"CREATE TABLE car_prices AS SELECT * FROM source_df")

def load_sqlite(data: pd.DataFrame):
    global sqlite, sqlite_cursor
    sqlite = sqlite3.connect(':memory:')
    data.to_sql('car_prices', sqlite, index=False)
    sqlite_cursor = sqlite.cursor()

def load_sqlite_idx(data: pd.DataFrame):
    global sqlite_idx, sqlite_idx_cursor
    sqlite_idx = sqlite3.connect(':memory:')
    data.to_sql('car_prices', sqlite_idx, index=False)
    sqlite_idx_cursor = sqlite_idx.cursor()
    for col in ["promo", "customer", "segment", "category", "product", "date", "orderid"]:
        sqlite_idx_cursor.execute(f"CREATE INDEX index_{col} ON car_prices ({col});")

# 3. data query methods
def query_pandas(loops=1000, filters:list[tuple[str, str]]| None = None) -> float:
    global df
    value = 0.0
    for _ in range(loops):
        filter = df[filters[0][0]] == filters[0][1]
        for f in filters[1:]:
            if isinstance(f[1], list):
                filter &= df[f[0]].isin(f[1])
            else:
                filter &= df[f[0]] == f[1]
        value += df[filter]['sales'].sum()
    return value

def query_nanocube_roaring(loops=1000, filters:list[tuple[str, str]]| None = None) -> float:
    global nc_r
    value = 0.0
    for _ in range(loops):
        f = dict(filters)
        value += nc_r.get('sales', **f)
    return value

def query_nanocube_numpy(loops=1000, filters:list[tuple[str, str]]| None = None) -> float:
    global nc_n
    value = 0.0
    for _ in range(loops):
        value += nc_n.get('sales', **dict(filters))
    return value

def query_polars(loops=1000, filters:list[tuple[str, str]]| None = None) -> float:
    global pl_df
    value = 0.0
    for _ in range(loops):
        filter = pl.col(filters[0][0]) == filters[0][1]
        for f in filters[1:]:
            if isinstance(f[1], list):
                filter &= pl.col(f[0]).is_in(f[1])
            else:
                filter &= pl.col(f[0]) == f[1]
        value += pl_df.filter(filter)['sales'].sum()
    return value

def query_arrow(loops=1000, filters:list[tuple[str, str]]| None = None) -> float:
    global pat
    value = 0.0
    for _ in range(loops):
        criteria = [
            pc.equal(pat[filters[0][0]], filters[0][1])
        ]
        for f in filters[1:]:
            if isinstance(f[1], list):
                criteria.append(pc.is_in(pat[f[0]], pa.array(f[1])))
            else:
                criteria.append(pc.equal(pat[f[0]], f[1]))
        combined_filter = criteria[0]
        for condition in criteria[1:]:
            combined_filter = pc.and_(combined_filter, condition)
        filtered_table = pat.filter(combined_filter)
        if filtered_table.num_rows > 0:
            value += pc.sum(filtered_table['sales']).as_py()
    return value

def query_duckdb(loops=1000, filters:list[tuple[str, str]]| None = None) -> float:
    global duckdb
    value = 0.0
    for _ in range(loops):
        criterias = []
        for f in filters:
            if isinstance(f[1], list):
                criterias.append(f"{f[0]} IN ({', '.join([f'\'{x}\'' for x in f[1]])})")
            elif f[1] == False:
                criterias.append(f"{f[0]}={f[1]}")
            else:
                criterias.append(f"{f[0]}='{f[1]}'")
        criteria = " AND ".join(criterias)
        result = duckdb.sql(f"SELECT SUM(sales) FROM car_prices WHERE {criteria};").fetchall()[0][0]
        if result is not None:
            value += result
    return value

def query_sqlite(loops=1000, filters:list[tuple[str, str]]| None = None) -> float:
    global sqlite_cursor
    value = 0.0
    for _ in range(loops):
        criterias = []
        for f in filters:
            if isinstance(f[1], list):
                criterias.append(f"{f[0]} IN ({', '.join([f'\'{x}\'' for x in f[1]])})")
            elif isinstance(f[1], bool):
                criterias.append(f"{f[0]}={f[1]}")
            else:
                criterias.append(f"{f[0]}='{f[1]}'")
        criteria = " AND ".join(criterias)
        sqlite_cursor.execute(f"SELECT SUM(sales) FROM car_prices WHERE {criteria};")
        result = sqlite_cursor.fetchone()[0]
        if result is not None:
            value += result
    return value

def query_sqlite_idx(loops=1000, filters:list[tuple[str, str]]| None = None) -> float:
    global sqlite_idx_cursor
    value = 0.0
    for _ in range(loops):
        criterias = []
        for f in filters:
            if isinstance(f[1], list):
                criterias.append(f"{f[0]} IN ({', '.join([f'\'{x}\'' for x in f[1]])})")
            elif isinstance(f[1], bool):
                criterias.append(f"{f[0]}={f[1]}")
            else:
                criterias.append(f"{f[0]}='{f[1]}'")
        criteria = " AND ".join(criterias)
        sqlite_idx_cursor.execute(f"SELECT SUM(sales) FROM car_prices WHERE {criteria};")
        result = sqlite_idx_cursor.fetchone()[0]
        if result is not None:
            value += result
    return value


class Benchmark:
    def __init__(self, max_rows=10_000_000, loops= 10, sorted=True):
        self.max_rows = max_rows
        self.loops = loops
        self.sorted = sorted
        self.data_template = {"pandas": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                     "nanocube_roaring": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "nanocube_numpy": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "polars": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "arrow": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "duckdb": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "sqlite": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "sqlite_idx": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "rows": [],
                        "duration" : [],
                        "count": {"s": [], "m": [], "l": [], "xl": [], "hk": [] }}
        self.data = self.data_template.copy()
        self.engines = ["pandas", "nanocube_roaring", "nanocube_numpy", "polars", "arrow", "duckdb", "sqlite", "sqlite_idx"]
        self.colors = ["black", "red", "orange", "blue", "green", "purple", "brown", "pink"]
        self.loaders = {
            "pandas": load_pandas,
            "nanocube_roaring": load_nanocube_roaring,
            "nanocube_numpy": load_nanocube_numpy,
            "polars": load_polars,
            "arrow": load_arrow,
            "duckdb": load_duckdb,
            "sqlite": load_sqlite,
            "sqlite_idx": load_sqlite_idx
        }
        self.queries = {
            "pandas": query_pandas,
            "nanocube_roaring": query_nanocube_roaring,
            "nanocube_numpy": query_nanocube_numpy,
            "polars": query_polars,
            "arrow": query_arrow,
            "duckdb": query_duckdb,
            "sqlite": query_sqlite,
            "sqlite_idx": query_sqlite_idx
        }

    def generate_data(self, rows):
        random.seed(4711)
        df = pd.DataFrame({'promo':    random.choices([True, False], k=rows),
                           'customer': random.choices(string.ascii_uppercase, weights=range(len(string.ascii_uppercase), 0, -1), k=rows),
                           'segment':  random.choices([f'S{i}' for i in range(10)], weights=range(10, 0, -1), k=rows),
                           'category': random.choices([f'C{i}' for i in range(100)], weights=range(100, 0, -1), k=rows),
                           'product':  random.choices([f'P{i}' for i in range(1000)], k=rows),
                           'date':     random.choices([datetime.date.today() - datetime.timedelta(days=i) for i in range(364)], k=rows),
                           'orderid':    random.choices([f'O{i}' for i in range(10000)], k=rows),
                           'sales':    [1 for _ in range(rows)],
                           'cost':     [1 for _ in range(rows)]})
        members = dict([(col, df[col].unique()) for col in df.columns])
        if self.sorted:
            df = df.sort_values(by=['promo', 'segment', 'customer', 'category', 'date', 'product', 'orderid'])
        return df, members

    def run(self):
        self.data = self.data_template.copy()
        data = self.data
        print("Running NanoCube benchmarks. Please wait (for a long time...")
        print("*" * 50)

        rows = 100  # we start with 100 rows
        while rows <= self.max_rows:
            print(f"Benchmark run with {rows:,} rows and {self.loops} loops:")
            b_start = datetime.datetime.now()

            # generate new data set with current row count
            df, members = self.generate_data(rows)
            data["rows"].append(rows)


            # initialize the engines
            print(f"\tEngine initialization from Pandas dataframe:")
            for engine in self.engines:
                start = datetime.datetime.now()
                self.loaders[engine](df)
                duration = (datetime.datetime.now() - start).total_seconds()
                print(f"\t\t'{engine}' in {duration:.5f} sec.")


            # query execution
            print(f"\tQuery execution with {self.loops}x loops on dataset with {rows:,} rows:")
            for size in ["s", "m", "l", "xl", "hk"]:
                filters, count = self.get_filters(size, members)
                data["count"][size].append(count)
                print(f"\t\tQuery of size '{size} returning {count:,} rows with filters: {filters}")

                for engine in self.engines:
                    start = datetime.datetime.now()
                    value = self.queries[engine](loops=self.loops, filters=filters)
                    duration = (datetime.datetime.now() - start).total_seconds()
                    print(f"\t\t\t'{engine}' in {duration:.5f} sec., returned value = {value:,.2f}")
                    data[engine][size].append(duration / self.loops)


            b_duration = (datetime.datetime.now() - b_start).total_seconds()
            print(f"Benchmark run with {rows:,} rows and {self.loops} loops "
                  f"finished in overall in {b_duration:.5f} sec.")
            rows = rows * 2

        # create charts
        postfix = " (sorted)" if self.sorted else ""
        self.create_query_chart(data, "s", "Single Row Point Query", "7 filter columns." + postfix)
        self.create_query_chart(data, "m", "Point Query, Sum Over ±0.1% Of Rows", "2 filters." + postfix )
        self.create_query_chart(data, "l", "Point Query, Sum Over ±5% Of Rows", "3 filters." + postfix)
        self.create_query_chart(data, "xl", "Point Query, Sum Over ±50% Of Rows", "1 filter." + postfix)
        self.create_query_chart(data, "hk", "Single Column High Card. Point Query", "2 filters." + postfix)

    def get_filters(self, size, members) -> (list[tuple[str, str]], int):
        global df, c_roaring
        pandas_query = ""
        cube_query = ""
        p_value = 0
        c_value = 0
        filters = []

        if size == "s":
            # get a single record
            record = (df.iloc[[0 + len(df.index) // 2]]).squeeze()[:-2].to_dict().items()
            # pandas query
            pandas_query = f"df[" + " & ".join([f"(df['{k}'] == '{v}')" if isinstance(v, str) else f"(df['{k}'] == {v.__repr__()})" for k, v in record]) + "]['sales'].sum()"
            p_value = eval(pandas_query)
            # cube query
            cube_query = f"nc_r.get('sales', " + ", ".join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v.__repr__()}" for k, v in reversed(record)]) + ")"
            c_value = eval(cube_query)
            # create filter
            filters = list(record)

        elif size == "m":
            # Query for ±0.1% of the records
            product = random.choice(members["product"])
            segment = random.choice(members["segment"])
            pandas_query = f"df[(df['product'] == '{product}') & (df['segment'] == '{segment}')]['sales'].sum()"
            p_value = eval(pandas_query)
            # cube query
            cube_query = f"nc_r.get('sales', product='{product}', segment='{segment}')"
            c_value = eval(cube_query)
            # create filter
            filters = [("product", product), ("segment", segment)]

        elif size == "l":
            # Query for ±5% of the records
            segment = random.choice(members["segment"])

            pandas_query = f"df[(df['promo'] == True) & (df['segment'] == '{segment}')]['sales'].sum()"
            cube_query = f"nc_r.get('sales', segment='{segment}', promo=True)"

            quote = "'"
            categories = [x for x in random.choices(members['category'], k=1)]
            categories_text = f"[{', '.join([quote + x + quote for x in random.choices(members['category'], k=1)])}, ]"
            pandas_query = (f"df[(df['promo'] == True) & "
                            f"(df['segment'] == '{segment}') & "
                            f"(df['category'].isin({categories})) ]['sales'].sum()")
            cube_query = f"nc_r.get('sales', segment='{segment}', category={categories_text}, promo=True)"  # , aggregate='min'
            p_value = eval(pandas_query)
            # cube query
            c_value = eval(cube_query)
            # create filter
            filters = [("promo", True), ("segment", segment), ("category", categories)]

        elif size == "xl":
            # Query for ±50% of the records
            pandas_query = f"df[(df['promo'] == True)]['sales'].sum()"
            p_value = eval(pandas_query)
            # cube query
            cube_query = f"nc_r.get('sales', promo=True)"
            c_value = eval(cube_query)
            # create filter
            filters = [("promo", True)]

        elif size == "hk":
            # Query for single column value with high cardinality
            product = random.choice(members["product"])
            order = random.choice(members["orderid"])
            pandas_query = f"df[(df['product'] == '{product}') & (df['orderid'] == '{order}')]['sales'].sum()"
            p_value = eval(pandas_query)
            # cube query
            cube_query = f"nc_r.get('sales', orderid='{order}', product='{product}')"
            c_value = eval(cube_query)
            # create filter
            filters = [("product", product), ("orderid", order)]


        # if p_value != c_value:
        #     raise ValueError(f"Upps, something went totally wrong: {p_value} != {c_value}") # this should never happen
        return filters, p_value


    def create_query_chart(self, data, size="s", title="Small", subtitle_postfix=""):
        # create the chart
        fig, ax = plt.subplots()
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel("Dataset size in rows")
        ax.set_ylabel("Duration (sec)")
        ax.grid(True)
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='grey')

        # primary y-axis (durations)
        for engine, color in zip(self.engines, self.colors):
            ax.plot(data["rows"], data[engine][size],
                    label=f"{engine.capitalize()}", linestyle='solid', color= color, marker="x")
        ax.legend(loc='upper left')

        # secondary y-axis (returned rows)
        ax2 = ax.twinx()
        ax2.set_yscale('log')
        ax2.plot(data["rows"], data["count"][size],
                 label=f"Returned rows", color='steelblue',
                 linestyle='dotted', marker=".")
        ax2.set_ylabel('# of returned rows', color='steelblue')
        ax2.get_yaxis().set_major_formatter(
            ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        ax2.legend(loc='lower right')

        # title
        plt.suptitle(title, fontsize=16)
        sub_title = f"Ø duration per query over N={self.loops} repetitions. " + subtitle_postfix
        plt.title(sub_title, fontsize=10)
        fig.savefig(f"charts/{size}{'_sorted' if self.sorted else ''}.png")
        plt.show()


if __name__ == "__main__":
    # run the benchmark
    #
    rows = 10_000_000
    Benchmark(max_rows=rows, sorted=False).run()
    Benchmark(max_rows=rows, sorted=True).run()

