# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from unittest import TestCase
from nanocube import cubed
from datetime import datetime


class TestCubeWithDates(TestCase):
    def setUp(self) -> None:
        data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "date": [datetime(2024, 6, 1), datetime(2024, 6, 2),
                     datetime(2024, 7, 1), datetime(2024, 7, 2),
                     datetime(2024, 12, 1), datetime(2023, 12, 2)],
            "mailing": [True, False, True, False, True, False],
            "customer": ["Peter", "Peter", "Paul", "Paul", "Mary", "Mary"],
            "ambiguous": ["A", "Paul", "Online", "Mary", datetime(2024, 6, 1), True],
            "revenue": [100, 150, 300, 200, 250, 350],
            "cost": [50, 90, 150, 100, 150, 175]
        }
        self.df = pd.DataFrame.from_dict(data)
        self.schema = {
            "dimensions": [
                {"column": "product"},
                {"column": "channel"},
                {"column": "date"},
                {"column": "mailing"}
            ],
            "measures": [
                {"column": "revenue"}
            ]
        }

    def test_cube_without_ambiguities(self):
        cdf = cubed(self.df, schema=self.schema)
        self.assertEqual(cdf.ambiguities == False, True)
        self.assertEqual(cdf.ambiguities == 0, True)
        self.assertEqual(any(cdf.ambiguities), False)

    def test_cube_with_ambiguities(self):
        cdf = cubed(self.df)
        self.assertEqual(cdf.ambiguities == True, True)
        self.assertEqual(cdf.ambiguities == 3, True)
        self.assertEqual(any(cdf.ambiguities), True)
        # print(cdf.ambiguities)
