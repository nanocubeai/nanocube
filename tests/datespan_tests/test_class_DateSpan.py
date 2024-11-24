# datespan_tests - Copyright (c)2024, Thomas Zeutschler, MIT license

import unittest
from datetime import datetime, timedelta, time

from nanocube.datespan import DateSpan


class TestDateSpan(unittest.TestCase):

    def setUp(self):
        self.jan = DateSpan(datetime(2023, 1, 1), datetime(2023, 1, 31, 23, 59, 59, 999999))
        self.feb = DateSpan(datetime(2023, 2, 1), datetime(2023, 2, 28, 23, 59, 59, 999999))
        self.mar = DateSpan(datetime(2023, 3, 1), datetime(2023, 3, 31, 23, 59, 59, 999999))
        self.jan_feb = DateSpan(datetime(2023, 1, 1), datetime(2023, 2, 28, 23, 59, 59, 999999))
        self.jan_feb_mar = DateSpan(datetime(2023, 1, 1), datetime(2023, 3, 31, 23, 59, 59, 999999))
        self.undef = DateSpan.undefined()

    def test_now(self):
        now = DateSpan.now()
        diff = now.start - datetime.now()
        self.assertTrue(diff < timedelta(microseconds=1000))

    def test_today(self):
        today = DateSpan.today()
        self.assertEqual(today.start.date(), datetime.now().date())
        self.assertEqual(today.end.date(), datetime.now().date())

    def test_undefined(self):
        self.assertTrue(self.undef.is_undefined)

    def test_contains(self):
        self.assertTrue(datetime(2023, 1, 15) in self.jan)
        self.assertFalse(datetime(2023, 2, 1) in self.jan)
        self.assertTrue(self.jan in self.jan_feb)
        self.assertFalse(self.feb in self.jan)

    def test_clone(self):
        clone = self.jan.clone()
        self.assertEqual(clone, self.jan)

    def test_overlaps_with(self):
        self.assertTrue(self.jan.overlaps_with(self.jan_feb))
        self.assertFalse(self.jan.overlaps_with(self.feb))

    def test_consecutive_with(self):
        self.assertTrue(self.jan.consecutive_with(self.feb))
        self.assertFalse(self.jan.consecutive_with(self.mar))

    def test_merge(self):
        merged = self.jan.merge(self.feb)
        self.assertEqual(merged, self.jan_feb)

    def test_intersect(self):
        intersected = self.jan.intersect(self.jan_feb)
        self.assertEqual(intersected, self.jan)
        self.assertTrue(self.jan.intersect(self.mar).is_undefined)

    def test_subtract(self):
        subtracted = self.jan_feb.subtract(self.jan)
        self.assertEqual(subtracted, self.feb)

    def test_with_time(self):
        result = self.jan.with_time(time(12, 34, 56))
        to_be = DateSpan(self.jan.start.replace(hour=12, minute=34, second=56),
                         self.jan.end.replace(hour=12, minute=34, second=56, microsecond=0))
        self.assertEqual(result, to_be)

    def test_with_start(self):
        new_start = datetime(2023, 1, 15)
        result = self.jan.with_start(new_start)
        self.assertEqual(result.start, new_start)

    def test_with_end(self):
        new_end = datetime(2023, 1, 15)
        result = self.jan.with_end(new_end)
        self.assertEqual(result.end, new_end)

    def test_with_date(self):
        new_date = datetime(2023, 1, 15)
        result = self.jan.with_date(new_date)
        self.assertEqual(result.start, new_date)
        self.assertEqual(result.end, new_date)

    def test_with_year(self):
        result = self.jan.with_year(2024)
        self.assertEqual(result.start.year, 2024)
        self.assertEqual(result.end.year, 2024)

    def test_full_millisecond(self):
        result = self.jan.full_millisecond
        self.assertEqual(result.start.microsecond % 1000, 0)
        self.assertEqual(result.end.microsecond % 1000, 999)

    def test_full_second(self):
        result = self.jan.full_second
        self.assertEqual(result.start.microsecond, 0)
        self.assertEqual(result.end.microsecond, 999999)

    def test_full_minute(self):
        result = self.jan.full_minute
        self.assertEqual(result.start.second, 0)
        self.assertEqual(result.end.second, 59)

    def test_full_hour(self):
        result = self.jan.full_hour
        self.assertEqual(result.start.minute, 0)
        self.assertEqual(result.end.minute, 59)

    def test_full_day(self):
        result = self.jan.full_day
        self.assertEqual(result.start.hour, 0)
        self.assertEqual(result.end.hour, 23)

    def test_full_week(self):
        result = self.jan.full_week
        self.assertEqual(result.start.weekday(), 0)
        self.assertEqual(result.end.weekday(), 6)

    def test_full_month(self):
        result = self.jan.full_month
        self.assertEqual(result.start.day, 1)
        self.assertEqual(result.end.day, 31)

    def test_full_quarter(self):
        result = self.jan.full_quarter
        self.assertEqual(result.start.month, 1)
        self.assertEqual(result.end.month, 3)

    def test_full_year(self):
        result = self.jan.full_year
        self.assertEqual(result.start.month, 1)
        self.assertEqual(result.end.month, 12)

    def test_ytd(self):
        result = self.jan.ytd
        self.assertEqual(result.start.month, 1)
        self.assertEqual(result.end, self.jan.end)

    def test_mtd(self):
        result = self.jan.mtd
        self.assertEqual(result.start.day, 1)
        self.assertEqual(result.end.day, self.jan.end.day)

    def test_qtd(self):
        result = self.jan.qtd
        self.assertEqual(result.start.day, 1)
        self.assertEqual(result.end.day, self.jan.end.day)

    def test_wtd(self):
        result = self.jan.wtd
        self.assertEqual(result.end.day, self.jan.end.day)

    def test_shift(self):
        result = self.jan.shift(months=1)
        self.assertEqual(result, self.feb)

    def test_shift_start(self):
        result = self.jan.shift_start(months=1)
        self.assertEqual(result.start, self.feb.start)

    def test_shift_end(self):
        result = self.jan.shift_end(months=1)
        self.assertEqual(result.end, self.feb.end)

    def test_set_start(self):
        new_start = datetime(2023, 1, 15)
        result = self.jan.set_start(day=15)
        self.assertEqual(result.start, new_start)

    def test_set_end(self):
        new_end = datetime(2023, 1, 15)
        result = self.jan.set_end(day=15)
        self.assertEqual(result.end, DateSpan(new_end).full_day.end)

    def test_set(self):
        new_date = datetime(2023, 1, 15)
        result = self.jan.set(day=15)
        self.assertEqual(result.start, DateSpan(new_date).full_day.start)
        self.assertEqual(result.end, DateSpan(new_date).full_day.end)

    def test_duration(self):
        self.assertAlmostEqual(self.jan.duration, 30.999988425925926, places=4)

    def test_to_tuple(self):
        self.assertEqual(self.jan.to_tuple(), (self.jan.start, self.jan.end))

    def test_eq(self):
        self.assertTrue(self.jan == self.jan)
        self.assertFalse(self.jan == self.feb)

    def test_gt(self):
        self.assertTrue(self.feb > self.jan)
        self.assertFalse(self.jan > self.feb)

    def test_ge(self):
        self.assertTrue(self.feb >= self.jan)
        self.assertTrue(self.jan >= self.jan)

    def test_lt(self):
        self.assertTrue(self.jan < self.feb)
        self.assertFalse(self.feb < self.jan)

    def test_le(self):
        self.assertTrue(self.jan <= self.feb)
        self.assertTrue(self.jan <= self.jan)

    def test_hash(self):
        self.assertEqual(hash(self.jan), hash((self.jan.start, self.jan.end)))

    def test_parse_start_end(self):
        result = DateSpan('2023-01-01', '2023-01-31')
        self.assertEqual(result, self.jan)

    def test_parse_start_end_text(self):
        result = DateSpan('January 2023', 'March 2023')
        self.assertEqual(result, self.jan_feb_mar)


if __name__ == '__main__':
    unittest.main()
