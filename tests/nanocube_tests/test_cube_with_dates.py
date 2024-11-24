# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from unittest import TestCase
from nanocube import Cube
from datetime import datetime


class TestCubeWithDates(TestCase):
    def setUp(self) -> None:
        data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "date": [datetime(2024, 6, 1), datetime(2024, 6, 2),
                     datetime(2024, 7, 1), datetime(2024, 7, 2),
                     datetime(2024, 12, 1), datetime(2023, 12, 2)],
            "sales": [100, 150, 300, 200, 250, 350]
        }
        self.df = pd.DataFrame.from_dict(data)
        self.schema = {
            "dimensions": [
                {"column": "product"},
                {"column": "channel"},
                {"column": "date"}
            ],
            "measures": [
                {"column": "sales"}
            ]
        }

    def test_slicing_with_exact_dates(self):
        cube = Cube(self.df, schema=self.schema)

        # dates not existing in the data should return 0
        value = cube.date[datetime(2019, 3, 24)]
        self.assertEqual(value, 0)
        value = cube.date["2019-03-24"]
        self.assertEqual(value, 0)

        # variants for slicing with single date spans
        value = cube["date:June 2024"]
        self.assertEqual(value, 100 + 150)  # all sales in June 2024
        value = cube.date["June 2024"]
        self.assertEqual(value, 100 + 150)  # all sales in June 2024
        value = cube.date.June_2024
        self.assertEqual(value, 100 + 150)  # all sales in June 2024

        # full year
        value = cube["date:2024"]
        self.assertEqual(value, 100 + 150 + 300 + 200 + 250)  # all sales in 2024

        # exact date with variants
        value = cube[datetime(2024, 6, 1)]
        self.assertEqual(value, 100)
        value = cube.date["2024-6-1"]
        self.assertEqual(value, 100)
        value = cube.date["2024/6/1"]
        self.assertEqual(value, 100)
        value = cube.date["2024.6.1"]
        self.assertEqual(value, 100)
        value = cube.date["June 1st, 2024"]
        self.assertEqual(value, 100)
