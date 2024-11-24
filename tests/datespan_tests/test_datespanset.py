# datespan_tests - Copyright (c)2024, Thomas Zeutschler, MIT license

import sys
from datetime import datetime, time
from unittest import TestCase

import numpy as np
import pandas as pd

from nanocube.datespan.date_span import DateSpan
from nanocube.datespan.date_span_set import DateSpanSet


# from nanocube_tests.datespan_tests.parser_old.en.tokenizer import Tokenizer


class TestDateTextParser(TestCase):
    def setUp(self):
        self.debug = self.is_debug()

    @staticmethod
    def is_debug():
        """Check if the debugger is active. Used to print debug information."""
        gettrace = getattr(sys, 'gettrace', None)
        return (gettrace() is not None) if (gettrace is not None) else False

    def test_initial_parse_using_dateutil(self):
        text = "2024-09-09"
        result = DateSpanSet(text)
        self.assertEqual(result[0][0], datetime(2024, 9, 9))

    def test_single_word(self):
        text = "today"
        result = DateSpanSet(text)
        self.assertEqual(result[0][0], datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
        self.assertEqual(result[0][1], datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999))

    def test_single_word_month(self):
        other_words = ["month", "quarter", "year", "week"]
        words = ["today", "yesterday", "tomorrow", "ytd", "mtd", "qtd", "wtd",
                 "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                 "january", "february", "march", "april", "may", "june",
                 "july", "august", "september", "october", "november", "december",
                 ]
        for word in words:
            try:
                result = DateSpanSet.parse(word)
                if self.debug:
                    print(f"DateSpanSet: {word}:")
                    for i, span in enumerate(result):
                        print(f"\t{i + 1:02d} = {span[0]} - {span[1]}")
                    print(f"\tSQL: {result.to_sql('order date')}")
            except Exception as e:
                self.fail(f"\tError: {e}")

    def test_to_function(self):

        dss = DateSpanSet("today")
        sql = dss.to_sql("order date")
        f_func = dss.to_function()
        f_lambda = dss.to_lambda()
        f_numpy = dss.to_df_lambda()
        n_array = np.array([datetime.now() for _ in range(100)], dtype=np.datetime64)
        dss = pd.DataFrame(n_array, columns=["order date"])

        self.assertEqual(f_func(datetime.now()), True)
        self.assertEqual(f_lambda(datetime.now()), True)
        result = f_numpy(dss["order date"])
        self.assertEqual(result.index.to_list(), [i for i in range(100)])

    def test_datespans(self):

        texts = [  # ("1st of January 2024", DateSpan(datetime(2024, 1, 1)).full_day),
            # ("1st day of January, February and March 2024", None),
            ("2007-12-24T18:21Z", DateSpan(datetime(2007, 12, 24, 18, 21)).full_minute),
            ("next 3 days", DateSpan.now().shift(days=1).full_day.shift_end(days=2)),
            ("last week", DateSpan.now().shift(days=-7).full_week),
            ("2010-01-01T12:00:00.001+02:00", DateSpan(datetime(2010, 1, 1, 12, 0, 0, 1000))),
            ("2007-08-31T16:47+00:00", DateSpan(datetime(2007, 8, 31, 16, 47)).full_minute),
            ("2008-02-01T09:00:22+05", DateSpan(datetime(2008, 2, 1, 9, 0, 22)).full_second),
            ("2009-01-01T12:00:00+01:00", DateSpan(datetime(2009, 1, 1, 12, 0), None).full_second),
            # ("3rd week of 2024", None),
            ("09.08.2024", DateSpan(datetime(2024, 9, 8)).full_day),
            ("2024/09/08", DateSpan(datetime(2024, 9, 8)).full_day),
            ("2024-09-08", DateSpan(datetime(2024, 9, 8)).full_day),
            ("19:00", DateSpan.now().with_time(time(19, 0)).full_minute),
            ("1:34:45", DateSpan.now().with_time(time(1, 34, 45)).full_second),
            ("1:34:45.123", DateSpan.now().with_time(time(1, 34, 45, 123000))),
            ("1:34:45.123456", DateSpan.now().with_time(time(1, 34, 45, 123456))),

        ]

        for text, target in texts:
            try:
                if self.debug:
                    print(f"\nTokens for '{text}':")
                dss = DateSpanSet(text)
                if target is not None:
                    self.assertEqual(dss[0], target, f"Error: {text}")
                if self.debug:
                    print(f"\tequal = {dss[0] == target}")
                    for pos, span in enumerate(dss):
                        print(f"\t{pos + 1:02d}: {span}")
            except Exception as e:
                if self.debug:
                    print(f"Error: {e}")
                else:
                    self.fail(f"Error: {e}")

    def test_advanced(self):
        samples = [
            "aug 15, 2023 YTD",
            "aug 15, 2023",
            "aug 15th, 2023",
            "June 1st, 2023",
            "Q4 last year", "Q3 2022", "3rd quarter of 2022",
            "Q2",  "June 2022",
            "1st quarter",
            "from 2024-09-01 to 2024-09-10",
            "ly", "py", "ny", "cy",
            "ltm",
            "r3m", "r42m", "r3w",
            "l4q",
            "this week",
            "last week",
            "next 3 months",
            "Jan, Feb and August of 2024",
            "2024 YTD",
            "yesterday",
            "2024-09-13",
            "between June and August 2023",
            "past 2 weeks",
            "this month",
            "from 2024-09-01 to 2024-09-15",
            "last week; next 3 months; Jan, Feb and August of 2024; from 2024-09-01 to 2024-09-15",
            "august last year",
            "today",
            "yesterday",
            "last week",
            "this month",
            "next 2 months",
            "from 2024-09-01 to 2024-09-15",
            "Jan, Feb and August of 2024",
            "MTD",
            "QTD",
            "YTD",
            "from 2024-09-01 14:00 to 2024-09-15 15:00",
            "between 2024-09-10 08:30 and 2024-09-10 17:45",
            "2024-09-05 12:00 to 14:00",
            "from 2024-09-15T09:00 to 2024-09-15T18:00",

            "since August 2024",
            "since 2024-08-15",
            "since 15.08.2024 14:00",
            "since 2024-08-15 14:00:00.123456",

            "2024-09-10 14:00:00.123",  # Milliseconds
            "2024-09-10 14:00:00.123456",  # Microseconds
            "from 2024-09-10 14:00:00.123 to 2024-09-10 15:00:00.789",
            "10/09/2024 14:00:00.123456",

            "between 09/01/2024 and 09/10/2024",
            "from 09.01.2024 to 09.10.2024",
            "between 2024-09-01 and 2024-09-10",

            "now",
            "every 1st Monday of YTD",
            "every 1st monday in YTD",
            "every Mon, Tue, Wed in this month",
            "every Mon, Tue, Wed of this month",
            "every Friday of next month",
            "every 2nd Friday of next month",
            "every Mon and Thu of this quarter",

            "every Mon, Wed, Fri of this month",
            "every 2nd Tuesday in next quarter",
            "every Friday of 2024",

            "today; yesterday; last week",

            # "ltm",
            # "py","cy","ly","ny",
            # "r1m","r2m","r3m","r4m","r5m","r6m","r7m","r8m","r9m","r10m", "r11m", "r12m", "r13m", "r14m", "r15m",
            # "r1q","r2q","r3q","r4q","r5q","r6q","r7q","r8q","r9q","r10q", "r11q", "r12q",
            # "r1y","r2y","r3y","r4y","r5y","r6y","r7y","r8y","r9y","r10y", "r11y", "r12y",
            # "r1w","r2w","r3w","r4w","r5w","r6w","r7w","r8w","r9w","r10w", "r11w", "r12w",
            # "r1d","r2d","r3d","r4d","r5d","r6d","r7d","r8d","r9d","r10d", "r11d", "r12d",
        ]

        # just test if the samples can be parsed without errors
        if self.debug:
            for sample in samples:
                print(f"Text: {sample}")
                try:
                    dss = DateSpanSet.parse(sample)
                    for span in dss:
                        print(f"\t{span}")
                    pass
                except Exception as e:
                    print(f"\tError: {e}")
        else:
            for sample in samples:
                try:
                    dss = DateSpanSet(sample)
                except Exception as e:
                    self.fail(f"Error: {e}")

    def test_parse_simple_datespans(self):

        texts = [
            ("last 3 month", DateSpan.now().shift(months=-1).full_month.shift_start(months=-2)),
            ("2024", DateSpan(datetime(2024, 1, 1)).full_year),
            ("past 3 month", DateSpan.now().shift_start(months=-3)),
            ("previous 3 month", DateSpan.now().shift(months=-1).full_month.shift_start(months=-2)),
            ("this quarter", DateSpan.now().full_quarter),
            ("this minute", DateSpan.now().full_minute),
            ("2024", DateSpan(datetime(2024, 1, 1)).full_year),
            ("March", DateSpan(datetime(datetime.now().year, 3, 1)).full_month),
            ("Jan 2024", DateSpan(datetime(2024, 1, 1)).full_month),
            ("last month", DateSpan(datetime.now()).full_month.shift(months=-1)),
            ("previous month", DateSpan(datetime.now()).full_month.shift(months=-1)),
            ("prev. month", DateSpan(datetime.now()).full_month.shift(months=-1)),
            ("actual month", DateSpan(datetime.now()).full_month),
            ("next month", DateSpan(datetime.now()).full_month.shift(months=1)),
            ("next year", DateSpan(datetime.now()).full_year.shift(years=1)),
            ("today", DateSpan(datetime.now()).full_day),
            ("yesterday", DateSpan(datetime.now()).shift(days=-1).full_day),
            ("ytd", DateSpan(datetime.now()).ytd),
        ]
        for text, test in texts:
            if self.debug:
                print(f"Text: {text}")
                print(f"\tExpected: {test}")

            try:
                as_is = DateSpanSet(text)[0]
            except Exception as e:
                if self.debug:
                    print(f"\tAs is: {as_is}")
                self.fail(f"Error: {e}")

            to_be = test
            almost_equal = as_is.almost_equals(test, epsilon=1_000_000)
            if not almost_equal:
                pass
            self.assertTrue(almost_equal, f"Error: {text}")

    def test_last_past_previous_rolling_variants(self):

        for relative in ["this", "last", "past", "previous", "next", "rolling"]:
            for unit in ["quarter", "year", "month", "week", "day", "hour", "minute", "second", "millisecond"]:
                for offset in range(1, 10):
                    if relative == "this":
                        text = f"{relative} {unit}"
                    else:
                        text = f"{relative} {offset} {unit}"
                    if self.debug:
                        print(f"Text: {text}")
                    dss = DateSpanSet(text)
                    if self.debug:
                        print(f"\t{dss}")
                    if relative == "this":
                        break
