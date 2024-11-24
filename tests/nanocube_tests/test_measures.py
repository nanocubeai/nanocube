# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
import numpy as np
import pandas as pd
from unittest import TestCase
from nanocube import Cube


class TestMeasures(TestCase):
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
                {"column": "product"},
                {"column": "channel"}
            ],
            "measures": [
                {"column": "sales"},
                {"column": "cost"}
            ]
        }

    def test_change_default_measure(self):
        cdf = Cube(self.df, schema=self.schema)

        self.assertEqual(cdf.A.Online, 100)
        cdf.schema.measures.default = "cost"
        self.assertEqual(cdf.A.Online, 50)

        with self.assertRaises(ValueError):
            cdf.schema.measures.default = "xxxxxxx"

    def test_measure_methods(self):
        cdf = Cube(self.df, schema=self.schema)

        x = cdf.Online.sales.sum

        self.assertEqual(cdf.Online.sales, 100 + 150 + 300)
        self.assertEqual(cdf.Online.sales.count, 3)
        self.assertEqual(cdf.Online.sales.sum, 100 + 150 + 300)
        self.assertEqual(cdf.Online.sales.mean, (100 + 150 + 300) / 3)
        self.assertEqual(cdf.Online.sales.min, 100)
        self.assertEqual(cdf.Online.sales.max, 300)
        self.assertEqual(cdf.Online.sales.std, np.std([100, 150, 300]))
        self.assertEqual(cdf.Online.sales.var, np.var([100, 150, 300]))
        self.assertEqual(cdf.Online.sales.median, 150)
