# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from unittest import TestCase
from nanocube import Cube


class TestCubeAliases(TestCase):
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
                {"column": "product", "alias": "dimp"},
                {"column": "channel", "alias": "dimc"}
            ],
            "measures": [
                {"column": "sales", "alias": "msrs"},
                {"column": "cost", "alias": "msrc"}
            ]
        }

    def test_cube_aliases(self):
        c = Cube(self.df, schema=self.schema)

        self.assertEqual(c.dimp.A.B.Online, 100 + 150)
        self.assertEqual(c.dimp.A.dimc.Online.msrc, 50)
