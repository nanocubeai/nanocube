# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from unittest import TestCase
from nanocube import cubed


class TestMembers(TestCase):
    def setUp(self) -> None:
        data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "sales": [100, 150, 300, 200, 250, 350],
            "cost": [50, 100, 200, 100, 150, 150]
        }
        self.df = pd.DataFrame.from_dict(data)

    def test_get_top_bottom_member(self):
        cdf = cubed(self.df)

        self.assertEqual(cdf.product.sales.top(2), ["C", "B"])
        self.assertEqual(cdf.product.sales.bottom(2), ["A", "B"])

        self.assertEqual(cdf.product.sales.top(100), ["C", "B", "A"])
        self.assertEqual(cdf.product.sales.bottom(100), ["A", "B", "C"])

        with self.assertRaises(ValueError):
            result = cdf.product.sales.top(0)

        with self.assertRaises(ValueError):
            result = cdf.sales.top(0)  # no dimension defined, just a measure


    def some_filter_function(self, row):
        return row["sales"] > 200
    def test_filter_members_by_lambda_function(self):
        cdf = cubed(self.df)

        self.assertEqual(cdf.product.sales.filter(self.some_filter_function), 300 + 250 + 350)
        self.assertEqual(cdf.product.sales.filter(lambda x: x["sales"] > 200), 300 + 250 + 350)

