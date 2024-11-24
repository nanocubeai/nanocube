# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from unittest import TestCase
from nanocube import Cube


class TestCubeContext(TestCase):
    def setUp(self) -> None:
        data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "sales": [100, 150, 300, 200, 250, 350],
            "cost": [50, 100, 200, 100, 150, 150]
        }
        self.df = pd.DataFrame.from_dict(data)
        self.schema = {
            "dimensions": [
                {"column": "product", "alias": "p"},
                {"column": "channel", "alias": "c"}
            ],
            "measures": [
                {"column": "sales"},
                {"column": "cost"}
            ]
        }

    def test_cube_context_dynamic_methods(self):
        c = Cube(self.df, schema=self.schema)

        self.assertEqual(c.A.B.Online, 100 + 150)

        self.assertEqual(c.A.B.Online, 100 + 150)
        self.assertEqual(c.A.Online + c.B.Online, 100 + 150)
        self.assertEqual(c.cost.A.B.Online, 50 + 100)
        self.assertEqual(c.product.A.B.Online, 100 + 150)
        self.assertEqual(c.product.A.B.channel.Online, 100 + 150)
        self.assertEqual(c.product.A.B.channel.Online.sales, 100 + 150)

        self.assertEqual(c.sales, 100 + 150 + 300 + 200 + 250 + 350)
        self.assertEqual(c.product, 100 + 150 + 300 + 200 + 250 + 350)
        self.assertEqual(c.product.A, 100 + 200)
        self.assertEqual(c.A, 100 + 200)
        self.assertEqual(c.A.Online, 100)
        self.assertEqual(c.A.Online.cost, 50)

        self.assertEqual(tuple(c.A.members.row_mask), tuple([0, 3]))
        self.assertEqual(tuple(c.A.row_mask), tuple([0, 3]))
        self.assertEqual(tuple(c.A.Online.row_mask), tuple([0]))

    def test_cube_context_slicer_methods(self):
        c = Cube(self.df, schema=self.schema)

        if not c.settings.ignore_key_errors:
            with self.assertRaises(ValueError):
                a = c["XXX"]
        with self.assertRaises(ValueError):
            a = c.xxx

        self.assertEqual(c["A, B, C"], 100 + 150 + 300 + 200 + 250 + 350)
        self.assertEqual(c["A, Online"], 100)
        self.assertEqual(c["A"], 100 + 200)

    def test_cube_context_dict_methods(self):
        c = Cube(self.df, schema=self.schema)

        self.assertEqual(c[{"product": "A"}], 100 + 200)
        self.assertEqual(c[{"product": ["A", "B"]}], 100 + 150 + 200 + 250)
        self.assertEqual(c[{"product": "A", "channel": "Online"}], 100)
        self.assertEqual(c[{"product": "A", "channel": ["Online", "Retail"]}], 100 + 200)
        self.assertEqual(c[{"product": ["A", "B"], "channel": ["Online", "Retail"]}], 100 + 150 + 200 + 250)

    def test_cube_context_dimension_list_methods(self):
        c = Cube(self.df, schema=self.schema)

        # 3 list variants: implicit tuple, explicit tuple, explicit list
        self.assertEqual(c.product["A", "B", "C"], 100 + 150 + 300 + 200 + 250 + 350)
        self.assertEqual(c.product["A", "B"], 100 + 150 + 200 + 250)

        self.assertEqual(c.product[("A", "B", "C")], 100 + 150 + 300 + 200 + 250 + 350)
        self.assertEqual(c.product[("A", "B")], 100 + 150 + 200 + 250)

        self.assertEqual(c.product[["A", "B", "C"]], 100 + 150 + 300 + 200 + 250 + 350)
        self.assertEqual(c.product[["A", "B"]], 100 + 150 + 200 + 250)

        # special case, non-existing members like 'XXX' will be ignored.
        self.assertEqual(c.product["A", "XXX"], 100 + 200)
        self.assertEqual(c.product[["A", "B", "XXX"]], 100 + 150 + 200 + 250)

        # special case, member list containing unhashable objects will raise ValueError
        if not c.settings.ignore_key_errors:
            with self.assertRaises(ValueError):
                a = c.product["A", {"not-exists": "XXX"}]  # unhashable object

    def test_cube_context_cube_list_methods(self):
        c = Cube(self.df, schema=self.schema)

        # 3 list variants: implicit tuple, explicit tuple, explicit list
        self.assertEqual(c["A", "B", "C"], 100 + 150 + 300 + 200 + 250 + 350)
        self.assertEqual(c["A", "B"], 100 + 150 + 200 + 250)

        self.assertEqual(c["A", "Online"], 100)
        self.assertEqual(c["A", "B", "Online"], 100 + 150)

        # special case: dimension content switch from 'product' to 'channel' to 'product'
        self.assertEqual(c["A", "Online", "B"], 0)  # no data, as intersection of 'A' and 'B' is always empty
        self.assertEqual(c["A", "Online", "A"], 100)  # intersection of 'A' and 'A' does not change the result

    def test_cube_context_with_dim_hints_methods(self):
        c = Cube(self.df, schema=self.schema)

        self.assertEqual(c["product:A, channel:Online"], 100)
        self.assertEqual(c["product:A, channel:Online, sales"], 100)

        self.assertEqual(c["product:A"], 100 + 200)
        self.assertEqual(c["product:A", "Online"], 100)
        self.assertEqual(c["product:A, Online"], 100)

    def test_cube_context_with_context_arguments(self):
        c = Cube(self.df, schema=self.schema)

        filter = c.A.Online
        self.assertEqual(c[filter, "cost"], 50)

        # define a context filter
        filter = c.A

        self.assertEqual(c[filter, "B", "Online"],
                         100 + 150)  # filter and 'B' are from the same dimension, so they get joined

        self.assertEqual(c[filter], 100 + 200)
        self.assertEqual(c[filter, "Online"], 100)
        self.assertEqual(c["Online", filter], 100)

        self.assertEqual(c["B", filter, "Online"], 250)

    def test_cube_boolean_context_operations(self):
        c = Cube(self.df, schema=self.schema)

        left = c.A
        right = c.B
        self.assertEqual(c[left | right], 100 + 150 + 200 + 250)  # OR > union
        self.assertEqual(c[left & right], 0)  # AND > intersection
        self.assertEqual(c[left ^ right], 100 + 150 + 200 + 250)  # XOR > symmetric difference
        self.assertEqual(c[~ left], 150 + 300 + 250 + 350)  # NOT > inversion

        result = left | right
        self.assertEqual(c[result], 100 + 150 + 200 + 250)  # OR > union

        left = c.A
        right = c.Online
        self.assertEqual(c[left | right], (100 + 150 + 300) + 200)  # OR > union
        self.assertEqual(c[left & right], 100)  # AND > intersection
        self.assertEqual(c[left ^ right], 150 + 300 + 200)  # XOR > symmetric difference

        self.assertEqual(c[right | left], (100 + 150 + 300) + 200)  # OR > union
        self.assertEqual(c[right & left], 100)  # AND > intersection
        self.assertEqual(c[right ^ left], 150 + 300 + 200)  # XOR > symmetric difference

    def context_equality(self, a, b):
        if not (a == b):
            self.failureException(
                f"Contexts are not equal: {a} ({a.__class__.__name__}) != {b} ({a.__class__.__name__})")

    def test_cube_comparison_operations(self):
        c = Cube(self.df, schema=self.schema)

        # self.addTypeEqualityFunc(Context, TestCubeContext.context_equality)
        # self.addTypeEqualityFunc(MeasureContext, TestCubeContext.context_equality)

        # Note: adding an underscore to any context will turn the context into a filter
        # and allow row-wise comparison operations in the underlying DataFrame

        # chained operations
        self.assertEqual(100 < c.sales_ < 200, 150)

        # filtering operations, indicated by using the underscore '_' as a suffix or keyword.
        self.assertEqual(c.sales_ < 250, 100 + 150 + 200)
        self.assertEqual(c.sales._ < 250, 100 + 150 + 200)

        # filtering operations
        self.assertEqual(c.sales_ < 200, 100 + 150)
        self.assertEqual(c.sales_ > 200, 250 + 300 + 350)
        self.assertEqual(c.sales_ <= 200, 100 + 150 + 200)
        self.assertEqual(c.sales_ >= 200, 200 + 250 + 300 + 350)
        self.assertEqual(c.sales_ == 200, 200)
        self.assertEqual(c.sales_ != 200, 100 + 150 + 250 + 300 + 350)

        # filtering operations on Online := [100, 150, 300] > directly
        self.assertEqual(c.Online_ < 200, 100 + 150)
        self.assertEqual(c.Online_ > 200, 300)
        self.assertEqual(c.Online_ <= 200, 100 + 150)
        self.assertEqual(c.Online_ >= 200, 300)
        self.assertEqual(c.Online_ == 200, 0)
        self.assertEqual(c.Online_ != 200, 100 + 150 + 300)

        # filtering operations on Online := [100, 150, 300] > indirectly
        self.assertEqual(c.Online.sales_ < 200, 100 + 150)
        self.assertEqual(c.Online.sales_ > 200, 300)
        self.assertEqual(c.Online.sales_ <= 200, 100 + 150)
        self.assertEqual(c.Online.sales_ >= 200, 300)
        self.assertEqual(c.Online.sales_ == 200, 0)
        self.assertEqual(c.Online.sales_ != 200, 100 + 150 + 300)

        # boolean operations on filters
        a = c.sales_ > 100
        b = c.sales_ < 200
        self.assertEqual(a & b, 150)
        self.assertEqual((c.sales_ > 100) & (c.sales_ < 200), 150)

        # chained operations
        self.assertEqual(100 < c.sales_ < 200, 150)

    def test_cube_comparison_operations_as_arguments(self):
        c = Cube(self.df, schema=self.schema)

        a = c.sales_ > 100  # 150, 300, 200, 250, 350
        b = c.sales_ < 200  # 100, 150

        self.assertEqual(c.Online[a], 150 + 300)
        self.assertEqual(c.Online[a & b], 150)

    def test_dimension_context_methods(self):
        c = Cube(self.df, schema=self.schema)

        self.assertEqual(c.product.members, ["A", "B", "C"])
        self.assertEqual(c.product.count, 3)
        self.assertEqual(c.product.unique, ["A", "B", "C"])

        self.assertEqual(c.channel.members, ["Online", "Retail"])
        self.assertEqual(c.channel.count, 2)
        self.assertEqual(c.channel.unique, ["Online", "Retail"])

        self.assertEqual(c.A.channel.members, ["Online", "Retail"])
        self.assertEqual(c.A.channel.count, 2)
        self.assertEqual(c.A.channel.unique, ["Online", "Retail"])

    def test_context_address(self):
        cdf = Cube(self.df, schema=self.schema)
        value = cdf.A.address
        address = cdf.product.A.address
        self.assertEqual(address, "A")
        address = cdf.product.A.B.address
        self.assertEqual(address, "B")

    def test_member_context_in_operator(self):
        cdf = Cube(self.df, schema=self.schema)
        self.assertTrue("A" in cdf.product)
        self.assertTrue("Online" in cdf.channel)
        self.assertFalse("XXX" in cdf.product)
        self.assertFalse("XXX" in cdf.channel)
