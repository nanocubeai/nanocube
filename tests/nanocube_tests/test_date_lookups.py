# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
import sys
import pandas as pd
from datetime import datetime, timedelta
from unittest import TestCase
from nanocube import cubed


class TestDateLookUps(TestCase):
    """
    Note: Tests for the slice method only need be callable and error free.
    """

    def setUp(self) -> None:
        self._debug: bool = False
        year = datetime.now().year

        data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "date": [datetime(year, 1, 1), datetime(year, 2, 1), datetime(year, 3, 1),
                     datetime(year, 6, 1), datetime(year, 7, 1), datetime(year, 11, 1)],
            "sales": [100, 150, 300, 200, 250, 350],
            "cost": [50, 100, 200, 100, 150, 150]
        }
        self.df = pd.DataFrame.from_dict(data)
        self.debug = self.is_debug()

    @staticmethod
    def is_debug():
        """Check if the debugger is active. Used to print debug information."""
        gettrace = getattr(sys, 'gettrace', None)
        return (gettrace() is not None) if (gettrace is not None) else False



    def test_standard_dateTime_tokens(self):
        c = cubed(self.df)
        tests = [
            ("Jan", 100),
            ("June", 200),
            ("July", 250),
            ("November", 350),
            ("1st quarter", 100 + 150 + 300),
        ]

        for test in tests:
            token, expected = test
            actual = c.date[token].sales
            self.assertEqual(actual, expected)

    def test_all_standard_dateTime_tokens(self):
        c = cubed(self.df)

        tokens = ["this minute", "last minute", "previous minute", "next minute", "this hour", "last hour",
                  "previous hour", "next hour",
                  "today", "yesterday", "tomorrow", "this year", "last year", "previous year", "next year",
                  "this month", "last month", "previous month", "next month",
                  "this week", "last week", "previous week", "next week",
                  "this quarter", "last quarter", "previous quarter", "next quarter"]

        for token in tokens:
            b = None
            if isinstance(token, tuple):
                token, b = token
            a = c.date[token]
            if self.debug:
                print(f"'{token}' = {a} = {b}")
            if b is not None:
                self.assertEqual(a, b)
