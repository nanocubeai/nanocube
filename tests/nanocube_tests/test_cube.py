# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from unittest import TestCase

from nanocube import Cube
from nanocube import cubed


class TestCube(TestCase):
    def setUp(self) -> None:
        data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "mailing": [True, True, False, False, True, False],
            "sales": [100, 150, 300, 200, 250, 350]
        }
        self.df = pd.DataFrame.from_dict(data)
        self.schema = {
            "dimensions": [
                {"column": "product", "caching": "EAGER"},
                {"column": "channel"}
            ],
            "measures": [
                {"column": "sales"}
            ]
        }

    def test_measures_only_cube(self):
        df = pd.DataFrame({"sales": [1, 2, 3]})
        cdf = cubed(df)
        self.assertEqual(cdf["sales"].avg, 2.0)
        self.assertEqual(cdf["*"], 6)
        self.assertEqual(cdf.sales, 6)
        self.assertEqual(cdf["sales"], 6)
        with self.assertRaises(ValueError):
            a = cdf[1] # there is no dimension

    def test_dims_and_schema_refer_same_column(self):
        df = pd.DataFrame({"sales": [1, 2, 3]})

        # create schema with single column used for both dimension and measure
        schema = {"dimensions": [{"column": "sales"}], "measures": [{"column": "sales"}]}

        cdf = cubed(df, schema)

        self.assertEqual(cdf[1], 1)
        self.assertEqual(cdf[2], 2)
        self.assertEqual(cdf[3], 3)

        self.assertEqual(cdf["sales"].avg, 2.0)
        self.assertEqual(cdf["*"], 6)
        self.assertEqual(cdf.sales, 6)
        self.assertEqual(cdf["sales"], 6)


        with self.assertRaises(ValueError):
            a = cdf[4] # there is no member 4 in dimension sales

    def test_dimension_only_cube(self):
        df = pd.DataFrame({"customer": ["A", "B", "C"]})
        cdf = cubed(df)
        # special case:
        # if no measures are defined, the cube will return the number of records
        # matching the given filter
        self.assertEqual(cdf["*"], 3)
        self.assertEqual(cdf.A, 1)
        self.assertEqual(cdf["B"], 1)


    def test_cube_access_methods(self):
        cdf = Cube(self.df, schema=self.schema)

        self.assertEqual(cdf[{"product": "A"}], 100 + 200)
        self.assertEqual(cdf["product:A"], 100 + 200)
        self.assertEqual(cdf["A"], 100 + 200)
        self.assertEqual(cdf.A, 100 + 200)

        self.assertEqual(cdf[{"product": ("A", "B")}], 100 + 200 + 150 + 250)
        self.assertEqual(cdf[("A", "B")], 100 + 200 + 150 + 250)
        self.assertEqual(cdf["A", "B"], 100 + 200 + 150 + 250)


    def test_boolean_dimension(self):
        cdf = cubed(self.df)

        self.assertEqual(cdf["mailing:True"], 100 + 150 + 250)
        self.assertEqual(cdf.mailing, 100 + 150 + 250)
        self.assertEqual(cdf.mailing[True], 100 + 150 + 250)
        self.assertEqual(cdf.mailing["TrUe"], 100 + 150 + 250)
        self.assertEqual(cdf.mailing[1], 100 + 150 + 250)
        self.assertEqual(cdf.mailing["yes"], 100 + 150 + 250)
        self.assertEqual(cdf.mailing["ON"], 100 + 150 + 250)
        # self.assertEqual(cdf.mailing_ == True, 100 + 150 + 250)


    def test_scalar_member_access(self):
        cube = Cube(self.df, schema=self.schema)

        value = cube["A"]
        self.assertEqual(value, 100 + 200)
        value = cube["B"]
        self.assertEqual(value, 150 + 250)
        value = cube["C"]
        self.assertEqual(value, 300 + 350)

        value = cube["Online"]
        self.assertEqual(value, 100 + 150 + 300)
        value = cube["Retail"]
        self.assertEqual(value, 200 + 250 + 350)

        value = cube["A", "Online"]
        self.assertEqual(value, 100)
        value = cube["B", "Retail"]
        self.assertEqual(value, 250)

        value = cube["A", "Online", "sales"]
        self.assertEqual(value, 100)
        value = cube["B", "Retail", "sales"]
        self.assertEqual(value, 250)

    def test_tuple_member_access(self):
        cube = Cube(self.df, schema=self.schema)

        value = cube[("A", "B")]
        self.assertEqual(value, 100 + 200 + 150 + 250)
        value = cube["A", "C"]
        self.assertEqual(value, 100 + 200 + 300 + 350)
        value = cube["A", "B", "C"]
        self.assertEqual(value, 100 + 200 + 150 + 250 + 300 + 350)

        value = cube["Online", "A", "B"]
        self.assertEqual(value, 100 + 150)
        value = cube["Online", "Retail"]
        self.assertEqual(value, 100 + 150 + 300 + 200 + 250 + 350)

        value = cube["Online", "Retail", "A", "C"]
        self.assertEqual(value, 100 + 200 + 300 + 350)

    def test_cube_primary_aggregations(self):
        cube = Cube(self.df, schema=self.schema)

        # A: 100 + 200 = 300
        self.assertEqual(cube["A"], 300)
        self.assertEqual(cube["A"].sum, 300)
        self.assertEqual(cube["A"].min, 100)
        self.assertEqual(cube["A"].max, 200)
        self.assertEqual(cube["A"].avg, 150)
        self.assertEqual(cube["A"].median, 150)
        self.assertEqual(cube["A"].std, 50)
        self.assertEqual(cube["A"].var, 2500)
        self.assertEqual(round(cube["A"].pof,5), round(300 / (100 + 150 + 300 + 200 + 250 + 350),5))

        self.assertEqual(cube["A"].count, 2)
        self.assertEqual(cube["A"].an, 2)
        self.assertEqual(cube["A"].nan, 0)
        self.assertEqual(cube["A"].zero, 0)
        self.assertEqual(cube["A"].nzero, 2)

    def test_cube_primary_aggregation_functions(self):
        cube = Cube(self.df, schema=self.schema)

        # A: 100 + 200 = 300
        self.assertEqual(cube["A"], 300)
        self.assertEqual(cube["A"].sum(), 300)
        self.assertEqual(cube["A"].min(), 100)
        self.assertEqual(cube["A"].max(), 200)
        self.assertEqual(cube["A"].avg(), 150)
        self.assertEqual(cube["A"].median(), 150)
        self.assertEqual(cube["A"].std(), 50)
        self.assertEqual(cube["A"].var(), 2500)
        self.assertEqual(round(cube["A"].pof(), 5), round(300 / (100 + 150 + 300 + 200 + 250 + 350), 5))

        self.assertEqual(cube["A"].count(), 2)
        self.assertEqual(cube["A"].an(), 2)
        self.assertEqual(cube["A"].nan(), 0)
        self.assertEqual(cube["A"].zero(), 0)
        self.assertEqual(cube["A"].nzero(), 2)


    def test_cube_primary_arithmetic(self):
        cube = Cube(self.df, schema=self.schema)

        self.assertEqual(cube["A"], 300)
        self.assertEqual(cube["B"], 400)

        # plus operators
        c = cube["A"] + 1
        self.assertEqual(c, 300 + 1)
        c = cube["A"] + cube["B"]
        self.assertEqual(c, 300 + 400)
        c = cube["A"] + cube["B"] + 1
        self.assertEqual(c, 300 + 400 + 1)
        c += 1
        self.assertEqual(c, 300 + 400 + 1 + 1)
        c += cube["B"]
        self.assertEqual(c, 300 + 400 + 1 + 1 + 400)

        # minus operators
        c = cube["A"] - 1
        self.assertEqual(c, 300 - 1)
        c = cube["A"] - cube["B"]
        self.assertEqual(c, 300 - 400)
        c = cube["A"] - cube["B"] - 1
        self.assertEqual(c, 300 - 400 - 1)
        c -= 1
        self.assertEqual(c, 300 - 400 - 1 - 1)
        c -= cube["B"]
        self.assertEqual(c, 300 - 400 - 1 - 1 - 400)

        # multiplication operators
        c = cube["A"] * 2
        self.assertEqual(c, 300 * 2)
        c = cube["A"] * cube["B"]
        self.assertEqual(c, 300 * 400)
        c = cube["A"] * cube["B"] * 2
        self.assertEqual(c, 300 * 400 * 2)
        c *= 2
        self.assertEqual(c, 300 * 400 * 2 * 2)
        c *= cube["B"]
        self.assertEqual(c, 300 * 400 * 2 * 2 * 400)

        # division operators
        c = cube["A"] / 2
        self.assertEqual(c, 300 / 2)
        c = cube["A"] / cube["B"]
        self.assertEqual(c, 300 / 400)
        c = cube["A"] / cube["B"] / 2
        self.assertEqual(c, 300 / 400 / 2)
        c /= 2
        self.assertEqual(c, 300 / 400 / 2 / 2)
        c /= cube["B"]
        self.assertEqual(c, 300 / 400 / 2 / 2 / 400)

        # modulo operators
        c = cube["A"] % 2
        self.assertEqual(c, 300 % 2)
        c = cube["A"] % cube["B"]
        self.assertEqual(c, 300 % 400)
        c = cube["A"] % cube["B"] % 2
        self.assertEqual(c, 300 % 400 % 2)

        # power operators
        c = cube["A"] ** 2
        self.assertEqual(c, 300 ** 2)

    def test_cube_secondary_arithmetic(self):
        cube = Cube(self.df, schema=self.schema)

        self.assertEqual(cube["A"], 300)
        self.assertEqual(cube["B"], 400)

        # (A, Online) = 100
        # (B, Online) = 150

        # plus operators
        c = cube["A"]["Online"] + 1
        self.assertEqual(c, 100 + 1)
        c = cube["A"]["Online"] + cube["B"]["Online"]
        self.assertEqual(c, 100 + 150)
        c = cube["A"]["Online"] + cube["B"]["Online"] + 1
        self.assertEqual(c, 100 + 150 + 1)
        c += 1
        self.assertEqual(c, 100 + 150 + 1 + 1)
        c += cube["B"]["Online"]
        self.assertEqual(c, 100 + 150 + 1 + 1 + 150)

        # minus operators
        c = cube["A"]["Online"] - 1
        self.assertEqual(c, 100 - 1)
        c = cube["A"]["Online"] - cube["B"]["Online"]
        self.assertEqual(c, 100 - 150)
        c = cube["A"]["Online"] - cube["B"]["Online"] - 1
        self.assertEqual(c, 100 - 150 - 1)
        c -= 1
        self.assertEqual(c, 100 - 150 - 1 - 1)
        c -= cube["B"]["Online"]
        self.assertEqual(c, 100 - 150 - 1 - 1 - 150)

        # multiplication operators
        c = cube["A"]["Online"] * 2
        self.assertEqual(c, 100 * 2)
        c = cube["A"]["Online"] * cube["B"]["Online"]
        self.assertEqual(c, 100 * 150)
        c = cube["A"]["Online"] * cube["B"]["Online"] * 2
        self.assertEqual(c, 100 * 150 * 2)
        c *= 2
        self.assertEqual(c, 100 * 150 * 2 * 2)
        c *= cube["B"]["Online"]
        self.assertEqual(c, 100 * 150 * 2 * 2 * 150)

        # division operators
        c = cube["A"]["Online"] / 2
        self.assertEqual(c, 100 / 2)
        c = cube["A"]["Online"] / cube["B"]["Online"]
        self.assertEqual(c, 100 / 150)
        c = cube["A"]["Online"] / cube["B"]["Online"] / 2
        self.assertEqual(c, 100 / 150 / 2)
        c /= 2
        self.assertEqual(c, 100 / 150 / 2 / 2)
        c /= cube["B"]["Online"]
        self.assertEqual(c, 100 / 150 / 2 / 2 / 150)

        # modulo operators
        c = cube["A"]["Online"] % 2
        self.assertEqual(c, 100 % 2)
        c = cube["A"]["Online"] % cube["B"]["Online"]
        self.assertEqual(c, 100 % 150)
        c = cube["A"]["Online"] % cube["B"]["Online"] % 2
        self.assertEqual(c, 100 % 150 % 2)

        # power operators
        c = cube["A"]["Online"] ** 2
        self.assertEqual(c, 100 ** 2)

    def test_cube_dynamic_access(self):
        cube = Cube(self.df, schema=self.schema)

        self.assertEqual(cube.A, 300)
        self.assertEqual(cube.A.sum, 300)
        self.assertEqual(cube.A.min, 100)
        self.assertEqual(cube.A.max, 200)
        self.assertEqual(cube.A.median, 150)
        self.assertEqual(cube.A.std, 50)
        self.assertEqual(cube.A.var, 2500)

        self.assertEqual(cube.A.count, 2)
        self.assertEqual(cube.A.an, 2)
        self.assertEqual(cube.A.nan, 0)
        self.assertEqual(cube.A.zero, 0)
        self.assertEqual(cube.A.nzero, 2)

        self.assertEqual(cube.A.Online, 100)
        self.assertEqual(cube.A.Online.sum, 100)
        self.assertEqual(cube.A.Online.min, 100)
        self.assertEqual(cube.A.Online.max, 100)
        self.assertEqual(cube.A.Online.median, 100)
        self.assertEqual(cube.A.Online.std, 0)
        self.assertEqual(cube.A.Online.var, 0)

        self.assertEqual(cube.A.Online.count, 1)
        self.assertEqual(cube.A.Online.an, 1)
        self.assertEqual(cube.A.Online.nan, 0)
        self.assertEqual(cube.A.Online.zero, 0)
        self.assertEqual(cube.A.Online.nzero, 1)

        self.assertEqual(cube.A.Retail, 200)
        self.assertEqual(cube.A.Retail.sum, 200)
        self.assertEqual(cube.A.Retail.min, 200)
        self.assertEqual(cube.A.Retail.max, 200)
        self.assertEqual(cube.A.Retail.median, 200)
        self.assertEqual(cube.A.Retail.std, 0)
        self.assertEqual(cube.A.Retail.var, 0)

        self.assertEqual(cube.A.Retail.count, 1)
        self.assertEqual(cube.A.Retail.an, 1)
        self.assertEqual(cube.A.Retail.nan, 0)
        self.assertEqual(cube.A.Retail.zero, 0)
        self.assertEqual(cube.A.Retail.nzero, 1)

    def test_cube_wildcard_access(self):
        cube = Cube(self.df, schema=self.schema)

        self.assertEqual(cube["channel:O*"], 100 + 150 + 300)
        self.assertEqual(cube["channel:*l*"], 100 + 150 + 300 + 200 + 250 + 350)

    def test_cube_address_to_args(self):
        cube = Cube(self.df, schema=self.schema)

        a = cube[cube.channel.Online, "A", "sales"].sum
        b = cube["A", "Online"]
        c = cube["A", "Online", "sales"]

        self.assertEqual(a, b)
        self.assertEqual(a, c)
