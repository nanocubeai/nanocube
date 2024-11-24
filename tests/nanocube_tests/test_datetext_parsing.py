from unittest import TestCase
from datetime import date, datetime

import numpy as np
import pandas as pd

from datespan import DateSpanSet, VERSION

class TestDateTextParser(TestCase):
    def setUp(self):
        self.debug = self.is_debug()

    @staticmethod
    def is_debug():
        import sys
        gettrace = getattr(sys, 'gettrace', None)
        if gettrace is None:
            return False
        else:
            v = gettrace()
            if v is None:
                return False
            else:
                return True

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
        words = ["today", "yesterday", "tomorrow", "week", "month", "quarter", "year", "ytd", "mtd", "qtd", "wtd",
                 "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                 "january", "february", "march", "april", "may", "june",
                 "july", "august", "september", "october", "november", "december",
                 ]
        for word in words:
            result = DateSpanSet(word)
            if self.debug or True:
                print(f"DateFilter: {word}:")
                for i, span in enumerate(result):
                    print(f"\t{i + 1:02d} = {span.start} - {span.end}")
                print(f"\tSQL: {result.to_sql('order date')}")

    def test_to_lambda_sql_function(self):

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

    def test_evaluate(self):
        datetexts = ["1st of January 2024",
                     "1st day of January, February and March 2024",
                     "last week",
                     "next 3 days",
                     "3rd week of 2024",
                     "08.09.2024", "2024/09/08", "2024-09-08",
                     "19:00", "1:34:45", "1:34:45.123", "1:34:45.123456",
                     "2007-08-31T16:47+00:00", "2007-12-24T18:21Z", "2008-02-01T09:00:22+05",
                     "2009-01-01T12:00:00+01:00", "2010-01-01T12:00:00.001+02:00"]

        for text in datetexts:
            try:
                dss = DateSpanSet(text)
                # if self.debug:
                #     print(f"\nTokens for '{text}':")
                #     for pos, span in enumerate(dss):
                #         print(f"{pos + 1:02d}: {span}")
            except Exception as e:
                if self.debug:
                    print(f"Error: {e}")
