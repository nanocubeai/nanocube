# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from unittest import TestCase

import pandas as pd
from nanocube import *


class TestCubedPandasLibrary(TestCase):
    def setUp(self) -> None:
        self.data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "sales": [100, 150, 300, 200, 250, 350]
        }
        self.df = pd.DataFrame.from_dict(self.data)

    def test_dataframe_cubed(self):
        df = pd.DataFrame(self.data)
        cdf = cubed(df)
        self.assertEqual(cdf.sales, 100 + 200 + 150 + 250 + 300 + 350)
        self.assertEqual(cubed(df).sales, 100 + 200 + 150 + 250 + 300 + 350)

    def test_method_cubed(self):
        df = pd.DataFrame(self.data)
        cdf = cubed(df)
        self.assertEqual(cdf.sales, 100 + 200 + 150 + 250 + 300 + 350)

