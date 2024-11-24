# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from unittest import TestCase
from nanocube import cubed


class TestCube(TestCase):
    def setUp(self) -> None:
        data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "sales": [100, 150, 300, 200, 250, 350]
        }
        self.df = pd.DataFrame.from_dict(data)
        self.schema = {"dimensions": [
            {"column": "product"},
            {"column": "channel"}
        ], "measures": [{"column": "sales"}]}

    def test_property_df(self):
        df = self.df
        cdf = cubed(self.df, schema=self.schema)
        self.assertTrue(df.equals(cdf.df))
        self.assertFalse(df.equals(cdf.A.df))
        self.assertTrue(df.equals(cdf["*"].df))
        self.assertFalse(df.equals(cdf["product:A"].df))

    def test_property_row_mask(self):
        cdf = cubed(self.df, schema=self.schema)
        self.assertEqual(list(cdf.A.row_mask), [0, 3])
        self.assertEqual(list(cdf.Online.row_mask), [0, 1, 2])
        self.assertEqual(list(cdf.A.Online.row_mask), [0])
        self.assertEqual(list(cdf.Retail.row_mask), [3, 4, 5])

    def test_property_mask_inv(self):
        cdf = cubed(self.df, schema=self.schema)
        self.assertEqual(list(cdf.A.row_mask_inverse), [1, 2, 4, 5])
        self.assertEqual(list(cdf.Online.row_mask_inverse), [3, 4, 5])
        self.assertEqual(list(cdf.A.Online.row_mask_inverse), [1, 2, 3, 4, 5])
        self.assertEqual(list(cdf.Retail.row_mask_inverse), [0, 1, 2])

