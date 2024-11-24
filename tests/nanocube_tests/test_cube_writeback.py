# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import pandas as pd
from unittest import TestCase

from nanocube.context.enums import ContextAllocation
from nanocube import cubed


class TestCubeWriteback(TestCase):
    def setUp(self) -> None:
        data = {
            "product": ["A", "B", "C", "A", "B", "C"],
            "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
            "sales": [100, 200, 400, 800, 1600, 3200]
        }
        self.df = pd.DataFrame.from_dict(data)

    def test_distribute_writeback(self):
        c = cubed(self.df, read_only=False)

        c.A.value = 450
        self.assertEqual(c.A, (100 + 800) / 2)
        c.A *= 4
        self.assertEqual(c.A, (100 + 800) * 2)
        c.A /= 2.0
        self.assertEqual(c.A, 100 + 800)
        c.A += 900
        self.assertEqual(c.A, (100 + 800) * 2)
        c.A -= 900
        self.assertEqual(c.A, 100 + 800)
        c.A %= 360  # modulo
        self.assertEqual(c.A, 20 + 160)
        c["A"] = 1800
        self.assertEqual(c.A, (100 + 800) * 2)

    def test_set_value_writeback(self):
        c = cubed(self.df, read_only=False)

        c.A.set_value(20, ContextAllocation.SET)
        self.assertEqual(c.A, 20 + 20)

    def test_delta_writeback(self):
        c = cubed(self.df, read_only=False)

        c.A.set_value(20, ContextAllocation.DELTA)
        self.assertEqual(c.A, 100 + 20 + 800 + 20)

    def test_set_multiply_writeback(self):
        c = cubed(self.df, read_only=False)

        c.A.set_value(2, ContextAllocation.MULTIPLY)
        self.assertEqual(c.A, (100 + 800) * 2)

    def test_set_zero_out_writeback(self):
        c = cubed(self.df, read_only=False)

        c.A.set_value(0, ContextAllocation.ZERO)
        self.assertEqual(c.A, 0)

    def test_set_nan_writeback(self):
        c = cubed(self.df, read_only=False)

        c.A.set_value(0, ContextAllocation.NAN)
        self.assertEqual(c.A, 0)
