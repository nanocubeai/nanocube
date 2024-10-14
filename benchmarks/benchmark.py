# nanocube - Copyright (c)2024, Thomas Zeutschler, MIT license
import random
import timeit
import string
import datetime
import matplotlib.pyplot as plt
from matplotlib import ticker
import pandas as pd
from rfc3986.abnf_regexp import segments

from nano_index import IndexingMethod
#from nanocube import NanoCube
from nanocube.nano_cube import NanoCube as NanoCube
#from nanocube.cube2 import Cube2

df: pd.DataFrame  | None = None
c_roaring: NanoCube | None = None
c_numpy: NanoCube | None = None

class Benchmark:
    def __init__(self, max_rows=10_000_000, loops= 10, sorted=True):
        self.max_rows = max_rows
        self.loops = loops
        self.sorted = sorted
        self.data = {"pandas": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "cube": {"s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "cube2": {"s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "rows": [],
                        "duration" : [],
                        "count": {"s": [], "m": [], "l": [], "xl": [], "hk": [] }}

    def generate_data(self, rows):
        random.seed(4711)
        df = pd.DataFrame({'promo':    random.choices([True, False], k=rows),
                           'customer': random.choices(string.ascii_uppercase, weights=range(len(string.ascii_uppercase), 0, -1), k=rows),
                           'segment':  random.choices([f'S{i}' for i in range(10)], weights=range(10, 0, -1), k=rows),
                           'category': random.choices([f'C{i}' for i in range(100)], weights=range(100, 0, -1), k=rows),
                           'product':  random.choices([f'P{i}' for i in range(1000)], k=rows),
                           'date':     random.choices([datetime.date.today() - datetime.timedelta(days=i) for i in range(364)], k=rows),
                           'order':    random.choices([f'O{i}' for i in range(10000)], k=rows),
                           'sales':    [1 for _ in range(rows)],
                           'cost':     [1 for _ in range(rows)]})
        members = dict([(col, df[col].unique()) for col in df.columns])
        if self.sorted:
            df = df.sort_values(by=['promo', 'segment', 'customer', 'category', 'date', 'product', 'order'])
        return df, members

    def run(self):
        # collect data
        global df, c_roaring, c_numpy

        self.data = {"pandas": { "s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "cube": {"s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "cube2": {"s": [], "m": [], "l": [], "xl": [], "hk": [] },
                        "rows": [],
                        "duration" : [],
                        "count": {"s": [], "m": [], "l": [], "xl": [], "hk": [] }}

        data = self.data
        print("Running benchmarks. Please wait...")

        rows = 100
        while rows <= self.max_rows:
            print(f"...with {rows:,} rows and {self.loops} loops", end="")
            b_start = datetime.datetime.now()

            # make the data
            df, members = self.generate_data(rows)
            data["rows"].append(rows)

            # make the cube
            start = datetime.datetime.now()
            c_roaring = NanoCube(df, caching=False, indexing_method=IndexingMethod.roaring)
            duration = (datetime.datetime.now() - start).total_seconds()
            data["duration"].append(duration)
            print(f", Roaring init in {duration:.5f} sec", end="")

            # make the cube2
            start = datetime.datetime.now()
            c_numpy = NanoCube(df, caching=False, indexing_method=IndexingMethod.numpy)
            duration = (datetime.datetime.now() - start).total_seconds()
            print(f", Numpy init in {duration:.5f} sec", end="")


            # small query
            for size in ["s", "m", "l", "xl", "hk"]:
                query_p, query_c, count = self.get_queries(size, members, rows)
                query_c2 = query_c.replace("c_roaring", "c_numpy")

                data["count"][size].append(count)
                data["pandas"][size].append(timeit.timeit(query_p, globals=globals(), number=self.loops) / self.loops)
                data["cube"][size].append(timeit.timeit(query_c, globals=globals(), number=self.loops) / self.loops)
                data["cube2"][size].append(timeit.timeit(query_c2, globals=globals(), number=self.loops) / self.loops)

            b_duration = (datetime.datetime.now() - b_start).total_seconds()
            print(f", overall in {b_duration:.5f} sec.")
            rows = rows * 2

        # create charts
        postfix = " (sorted)" if self.sorted else ""
        self.create_query_chart(data, "s", "Single Row Point Query", "7 filter columns." + postfix)
        self.create_query_chart(data, "m", "Point Query, Sum Over ±0.1% Of Rows", "2 filters." + postfix )
        self.create_query_chart(data, "l", "Point Query, Sum Over ±5% Of Rows", "3 filters." + postfix)
        self.create_query_chart(data, "xl", "Point Query, Sum Over ±50% Of Rows", "1 filter." + postfix)
        self.create_query_chart(data, "hk", "Single Column High Card. Point Query", "2 filters." + postfix)

        self.create_maketime_chart(data)

    def get_queries(self, size, members, rows):
        # 1. small point query, like returning only 1 record
        global df, c_roaring
        pandas_query = ""
        cube_query = ""
        p_value = 0
        c_value = 0

        if size == "s":
            # get a single record
            record = (df.iloc[[0 + len(df.index) // 2]]).squeeze()[:-2].to_dict().items()
            # pandas query
            pandas_query = f"df[" + " & ".join([f"(df['{k}'] == '{v}')" if isinstance(v, str) else f"(df['{k}'] == {v.__repr__()})" for k, v in record]) + "]['sales'].sum()"
            p_value = eval(pandas_query)
            # cube query
            cube_query = f"c_roaring.get('sales', " + ", ".join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v.__repr__()}" for k, v in reversed(record)]) + ")"
            c_value = eval(cube_query)

        elif size == "m":
            # Query for ±0.1% of the records
            product = random.choice(members["product"])
            segment = random.choice(members["segment"])
            pandas_query = f"df[(df['product'] == '{product}') & (df['segment'] == '{segment}')]['sales'].sum()"
            p_value = eval(pandas_query)
            # cube query
            cube_query = f"c_roaring.get('sales', product='{product}', segment='{segment}')"
            c_value = eval(cube_query)

        elif size == "l":
            # Query for ±5% of the records
            segment = random.choice(members["segment"])

            pandas_query = f"df[(df['promo'] == True) & (df['segment'] == '{segment}')]['sales'].sum()"
            cube_query = f"c_roaring.get('sales', segment='{segment}', promo=True)"

            quote = "'"
            categories = f"[{', '.join([quote + x + quote for x in random.choices(members['category'], k=1)])}, ]"
            pandas_query = (f"df[(df['promo'] == True) & "
                            f"(df['segment'] == '{segment}') & "
                            f"(df['category'].isin({categories})) ]['sales'].sum()")
            cube_query = f"c_roaring.get('sales', segment='{segment}', category={categories}, promo=True)"  # , aggregate='min'
            p_value = eval(pandas_query)
            # cube query
            c_value = eval(cube_query)

        elif size == "xl":
            # Query for ±50% of the records
            pandas_query = f"df[(df['promo'] == True)]['sales'].sum()"
            p_value = eval(pandas_query)
            # cube query
            cube_query = f"c_roaring.get('sales', promo=True)"
            c_value = eval(cube_query)

        elif size == "hk":
            # Query for single column value with high cardinality
            product = random.choice(members["product"])
            order = random.choice(members["order"])
            pandas_query = f"df[(df['product'] == '{product}') & (df['order'] == '{order}')]['sales'].sum()"
            p_value = eval(pandas_query)
            # cube query
            cube_query = f"c_roaring.get('sales', order='{order}', product='{product}')"
            c_value = eval(cube_query)


        if p_value != c_value:
            raise ValueError(f"Upps, something went totally wrong: {p_value} != {c_value}") # this should never happen
        return pandas_query, cube_query, p_value


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
        ax.plot(data["rows"], data["pandas"][size],
                label=f"Pandas", color="black",
                linestyle='dashed', marker="x")
        ax.plot(data["rows"], data["cube"][size],
                label=f"NanoCube(Roaring)", color="black",
                linestyle='solid', marker=".")
        ax.plot(data["rows"], data["cube2"][size],
                label=f"NanoCube(Numpy)", color="black",
                linestyle='dotted', marker=".")
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

    def create_maketime_chart(self, data):
        # create the chart
        fig, ax = plt.subplots()
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel("Dataset size in rows")
        ax.set_ylabel("Duration (sec)")
        ax.grid(True)
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='grey')

        # primary y-axis (durations)
        ax.plot(data["rows"], data["duration"],
                label=f"NanoCube", color="black",
                linestyle='solid', marker=".")
        ax.legend()

        # title
        plt.suptitle("NanoCube Initialization Time", fontsize=16)
        ops =  int(data["rows"][-1] / data["duration"][-1])
        sub_title = f"From existing Pandas DataFrame with Ø {ops:,} rows/sec."
        plt.title(sub_title, fontsize=10)
        fig.savefig(f"charts/init{'_sorted' if self.sorted else ''}.png")
        plt.show()


if __name__ == "__main__":
    # run the benchmark
    #
    rows = 1_000_000
    Benchmark(max_rows=rows, sorted=False).run()
    Benchmark(max_rows=rows, sorted=True).run()

