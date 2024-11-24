# datespan_tests - Copyright (c)2024, Thomas Zeutschler, MIT license

import unittest
from datetime import datetime

from nanocube.datespan.date_span import DateSpan
from nanocube.datespan.date_span_set import DateSpanSet


class TestDateSpanSet(unittest.TestCase):

    def setUp(self):
        self.jan = DateSpan(datetime(2023, 1, 1), datetime(2023, 1, 31, 23, 59, 59, 999999))
        self.feb = DateSpan(datetime(2023, 2, 1), datetime(2023, 2, 28, 23, 59, 59, 999999))
        self.mar = DateSpan(datetime(2023, 3, 1), datetime(2023, 3, 31, 23, 59, 59, 999999))
        self.jan_feb = DateSpanSet([self.jan, self.feb])
        self.jan_feb_mar = DateSpanSet([self.jan, self.feb, self.mar])
        self.empty_set = DateSpanSet()

    def test_init(self):
        dss = DateSpanSet("last month")
        self.assertIsInstance(dss, DateSpanSet)

    def test_iter(self):
        spans = list(self.jan_feb)
        self.assertEqual(len(spans), 1)

    def test_len(self):
        self.assertEqual(len(self.jan_feb), 1)

    def test_getitem(self):
        self.assertEqual(self.jan_feb[0], self.jan_feb._spans[0])

    def test_str(self):
        self.assertEqual(str(self.jan_feb), repr(self.jan_feb))

    def test_repr(self):
        self.assertTrue(repr(self.jan_feb).startswith("DateSpanSet("))

    @unittest.skip("Not implemented")
    def test_add(self):
        combined = self.jan_feb + self.mar
        self.assertIn(self.jan_feb_mar, combined)

    @unittest.skip("Not implemented")
    def test_sub(self):
        intersected = self.jan_feb - self.jan
        self.assertNotIn(self.feb, intersected)

    def test_eq(self):
        self.assertTrue(self.jan_feb == DateSpanSet([self.jan, self.feb]))
        self.assertFalse(self.jan_feb == self.mar)

    def test_ne(self):
        self.assertTrue(self.jan_feb != self.mar)

    def test_lt(self):
        self.assertTrue(self.jan_feb < DateSpanSet([self.mar]))

    def test_le(self):
        self.assertTrue(self.jan_feb <= DateSpanSet([self.mar]))

    def test_gt(self):
        self.assertTrue(DateSpanSet([self.mar]) > self.jan_feb)

    def test_ge(self):
        self.assertTrue(DateSpanSet([self.mar]) >= self.jan_feb)

    def test_contains(self):
        self.assertIn(self.jan, self.jan_feb)
        self.assertNotIn(self.mar, self.jan_feb)

    def test_bool(self):
        self.assertTrue(self.jan_feb)
        self.assertFalse(self.empty_set)

    def test_hash(self):
        self.assertEqual(hash(self.jan_feb), hash(DateSpanSet("Jan, Feb 2023")))

    def test_copy(self):
        clone = self.jan_feb.__copy__()
        self.assertEqual(clone, self.jan_feb)

    def test_start(self):
        self.assertEqual(self.jan_feb.start, self.jan.start)

    def test_end(self):
        self.assertEqual(self.jan_feb.end, self.feb.end)

    def test_clone(self):
        clone = self.jan_feb.clone()
        self.assertEqual(clone, self.jan_feb)

    @unittest.skip("Not implemented")
    def test_add_method(self):
        self.jan_feb.add(self.mar)
        self.assertIn(self.mar, self.jan_feb)

    @unittest.skip("Not implemented")
    def test_remove(self):
        self.jan_feb.remove(self.jan)
        self.assertNotIn(self.jan, self.jan_feb)

    @unittest.skip("Not implemented")
    def test_shift(self):
        shifted = self.jan_feb.shift(months=1)
        self.assertEqual(shifted[0].start.month, 2)

    def test_parse(self):
        dss = DateSpanSet.parse("last month")
        self.assertIsInstance(dss, DateSpanSet)

    def test_try_parse(self):
        dss = DateSpanSet.try_parse("last month")
        self.assertIsInstance(dss, DateSpanSet)
        dss = DateSpanSet.try_parse("invalid")
        self.assertIsNone(dss)

    def test_to_sql(self):
        sql = self.jan_feb.to_sql("date")
        self.assertIn("BETWEEN", sql)

    def test_to_function(self):
        func = self.jan_feb.to_function()
        self.assertTrue(callable(func))

    def test_to_lambda(self):
        func = self.jan_feb.to_lambda()
        self.assertTrue(callable(func))

    def test_to_df_lambda(self):
        func = self.jan_feb.to_df_lambda()
        self.assertTrue(callable(func))

    def test_to_tuples(self):
        tuples = self.jan_feb.to_tuples()
        self.assertEqual(tuples, [(self.jan.start, self.feb.end)])

    def test_filter(self):
        import pandas as pd
        df = pd.DataFrame({
            "date": [datetime(2023, 1, 15), datetime(2023, 2, 15), datetime(2023, 3, 15)]
        })
        filtered = self.jan_feb.filter(df, "date")
        self.assertEqual(len(filtered), 2)

    def test_merge(self):
        test = self.jan_feb.merge(self.mar)
        self.assertEqual(test, self.jan_feb_mar)

    def test_intersect(self):
        with self.assertRaises(NotImplementedError):
            self.jan_feb.intersect(self.mar)

    def test_invalid_text(self):
        with self.assertRaises(Exception):
            a = DateSpanSet("invalid text")


if __name__ == '__main__':
    unittest.main()
