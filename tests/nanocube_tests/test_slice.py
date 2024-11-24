# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from unittest import TestCase
from nanocube import cubed


class TestSlice(TestCase):
    """
    Note: Tests for the slice method only need be callable and error free.
    """
    def setUp(self) -> None:
        self._debug: bool = False
        data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "sales": [100, 150, 300, 200, 250, 350],
            "cost": [50, 100, 200, 100, 150, 150]
        }
        self.df = pd.DataFrame.from_dict(data)

    def test_default_slice(self):
        c = cubed(self.df)

        slice = c.slice()
        if self._debug:
            print("\nslice:\n{slice}")

    def test_custom_slice(self):
        c = cubed(self.df)

        slice = c.slice(rows="product", columns="channel", measures="sales", aggfunc="sum")
        if self._debug:
            print(f"\nslice:\n{slice}")

        slice = c.slice(rows="product, channel")
        if self._debug:
            print(f"\nslice:\n{slice}")

        slice = c.slice(rows=["product", "channel"])
        if self._debug:
            print(f"\nslice:\n{slice}")

        slice = c.slice(rows=[c.product, "channel"])
        if self._debug:
            print(f"\nslice:\n{slice}")

    def test_filter_slice(self):
        c = cubed(self.df)

        slice = c.slice(rows=[c.sales_ > 200, "channel"])  # should return channels Online, Retail onl
        if self._debug:
            print(f"\nslice:\n{slice}")

        slice = c.slice(rows=[c.product_ > 200, "channel"])  # should return products B, C
        if self._debug:
            print(f"\nslice:\n{slice}")

        slice = c.slice(rows=[c.product.A.B, "channel"])  # should return products A, B
        if self._debug:
            print(f"\nslice:\n{slice}")
