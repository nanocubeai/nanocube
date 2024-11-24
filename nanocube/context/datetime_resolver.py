# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Any

from dateutil.parser import parse, ParserError


def resolve_datetime(value: Any) -> (datetime | None, datetime | None):
    """
    A simple resolver for datetime information, e.g. `June`, `2024`, `2024-06`, `2024-06-01`,
    `2024-06-01 12:00:00` but also this year, last year, next year, yesterday, tomorrow, etc.
    String values will be parsed using dateutil.parser.parse method.

    If the value represents a specific date, it will return a tuple of a datetime and None.
    If the value represents a date range, it will return a tuple of first and last datetime in the range
    if the value does not represent a date, it will return a tuple (None, None).

    :param value: The datetime value to parse
    :return: a tuple of datetime objects
    """
    try:
        # Already a datetime object?
        if isinstance(value, datetime):
            return value, None
        if isinstance(value, timedelta):
            return datetime.now(), datetime.now() + value

        # Check for intervals given as tuples or lists
        if isinstance(value, (tuple, list)):
            if len(value) >= 2:
                return resolve_datetime(value[0])[0], resolve_datetime(value[1])[0]

        # Check for intervals is defined by a dictionary
        if isinstance(value, dict):
            if "from" in value and "to" in value:
                return resolve_datetime(value["from"])[0], resolve_datetime(value["to"])[0]
            if "from" in value:
                return resolve_datetime(value["from"])[0], datetime.max
            if "to" in value:
                return datetime.min, resolve_datetime(value["to"])[0]

        if not isinstance(value, (str, int, float)):
            return None, None

        # Integers and floats can be timestamps or years
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        if isinstance(value, int):
            if value < 0:
                return None, None
            if datetime.min.year <= value <= datetime.max.year:
                return datetime(year=value, month=1, day=1), datetime(year=value, month=12, day=31, hour=23, minute=59,
                                                                      second=59, microsecond=999999)
            if datetime.min.timestamp() <= value <= datetime.max.timestamp():
                return datetime.fromtimestamp(value), None
        if isinstance(value, float):
            if datetime.min.timestamp() <= value <= datetime.max.timestamp():
                return datetime.fromtimestamp(value), None
            else:
                raise ValueError(f"Invalid timestamp value {value}")

        # try to parse standard date strings/tokens, e.g.: today, yesterday, tomorrow, this year, last year, next year...
        standard_token, from_date, to_date = parse_standard_date_token(value)

        # Try to parse a date string
        try:
            dt = parse(value)

            # Check if the date has been guessed by dateutil.parser
            year_pos = value.find(str(dt.year))
            month_num_pos = value.find(str(dt.month))
            day_num_pos = value.find(str(dt.day))

            d_now = datetime.now().day

            if d_now == dt.day and (year_pos == -1 or month_num_pos == -1 or day_num_pos == -1):
                # It seems to be a guessed date.
                # Do not trust this.
                weekday, last = calendar.monthrange(dt.year, dt.month)
                return datetime(year=dt.year, month=dt.month, day=1), datetime(year=dt.year, month=dt.month, day=last,
                                                                               hour=23, minute=59, second=59,
                                                                               microsecond=999999)

            # check for month names
            month_short_name_pos = str(value).lower().find(dt.strftime("%b").lower())
            month_long_name_pos = str(value).lower().find(dt.strftime("%B").lower())
            if month_short_name_pos > -1 or month_long_name_pos > -1:
                if day_num_pos == -1 or month_num_pos >= year_pos:
                    # no date given, just a month name and maybe a year
                    # get the first and last day of the month
                    weekday, last = calendar.monthrange(dt.year, dt.month)
                    return datetime(year=dt.year, month=dt.month, day=1), datetime(year=dt.year, month=dt.month,
                                                                                   day=last, hour=23, minute=59,
                                                                                   second=59, microsecond=999999)

            return dt, None

        except ParserError as e:
            # Failed to parse the date
            return None, None

    except Exception as e:
        # Whatever happened, it's not seem to be a date...
        return None, None


def parse_standard_date_token(value, language="en") -> (bool, datetime | None, datetime | None):
    """
    Parse standard date strings like `today`, `yesterday`, `this year`, `last year`, `next year` etc.
    
    Arguments:
        value: The date string to parse.
        language: The 2-digit ISO 639 language to use for the parser (default: "en").
            If ISO 3166 codes are handed in, e.g. "en_US", then the 2-digit language, e.g. "en", is used as fallback.

        
    Returns: 
        A tuple containing of a boolean indicating if the value is a standard 
        date string, the start and end date of the range.
    """

    # region Standard date methods

    def this_minute():
        return (datetime.now().replace(second=0, microsecond=0),
                datetime.now().replace(second=59, microsecond=999999))

    def last_minute():
        return (datetime.now().replace(second=0, microsecond=0) - timedelta(minutes=1),
                datetime.now().replace(second=59, microsecond=999999) - timedelta(minutes=1))

    def next_minute():
        return (datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1),
                datetime.now().replace(second=59, microsecond=999999) + timedelta(minutes=1))

    def this_hour():
        return (datetime.now().replace(minute=0, second=0, microsecond=0),
                datetime.now().replace(minute=59, second=59, microsecond=999999))

    def last_hour():
        return (datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                datetime.now().replace(minute=59, second=59, microsecond=999999) - timedelta(hours=1))

    def next_hour():
        return (datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1),
                datetime.now().replace(minute=59, second=59, microsecond=999999) + timedelta(hours=1))

    def today():
        return (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999))

    def yesterday():
        return (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1),
                datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999) - timedelta(days=1))

    def tomorrow():
        return (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1),
                datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999) + timedelta(days=1))

    def this_year():
        return (datetime(datetime.now().year, 1, 1),
                datetime(datetime.now().year, 12, 31, 23, 59, 59, 999999))

    def last_year(years: int = 1):
        return (datetime(datetime.now().year - years, 1, 1),
                datetime(datetime.now().year - 1, 12, 31, 23, 59, 59, 999999))

    def next_year(years: int = 1):
        return (datetime(datetime.now().year + 1, 1, 1),
                datetime(datetime.now().year + years, 12, 31, 23, 59))

    def this_month():
        return (datetime(datetime.now().year, datetime.now().month, 1),
                datetime(datetime.now().year, datetime.now().month,
                         calendar.monthrange(datetime.now().year, datetime.now().month)[1], 23, 59, 59, 999999))

    def last_month(months: int = 1):
        today = datetime.now()
        last_month = today - relativedelta(months=1)
        first_month = today - relativedelta(months=months)
        date_from = first_month.replace(day=1)
        date_to = last_month + relativedelta(day=31)
        return date_from, date_to

    def next_month(months: int = 1):
        today = datetime.now()
        first_month = today + relativedelta(months=1)
        last_month = today + relativedelta(months=months)
        date_from = first_month.replace(day=1)
        date_to = last_month + relativedelta(day=31)
        return date_from, date_to

    def this_week():
        today = datetime.now()
        return today - timedelta(days=today.weekday()), today + timedelta(days=6 - today.weekday())

    def last_week():
        today = datetime.now()
        return today - timedelta(days=today.weekday() + 7), today - timedelta(days=today.weekday() + 1)

    def next_week():
        today = datetime.now()
        return today + timedelta(days=7 - today.weekday()), today + timedelta(days=13 - today.weekday())

    def this_quarter():
        today = datetime.now()
        quarter = (today.month - 1) // 3 + 1
        return (datetime(today.year, 3 * quarter - 2, 1),
                datetime(today.year, 3 * quarter,
                         calendar.monthrange(today.year, 3 * quarter)[1], 23, 59, 59, 999999))

    def last_quarter():
        today = datetime.now()
        quarter = (today.month - 1) // 3 + 1
        last_quarter = quarter - 1
        if last_quarter == 0:
            last_quarter = 4
        return (datetime(today.year, 3 * last_quarter - 2, 1),
                datetime(today.year, 3 * last_quarter,
                         calendar.monthrange(today.year, 3 * last_quarter)[1], 23, 59, 59, 999999))

    def next_quarter():
        today = datetime.now()
        quarter = (today.month - 1) // 3 + 1
        next_quarter = quarter + 1
        if next_quarter == 5:
            next_quarter = 1
        return (datetime(today.year, 3 * next_quarter - 2, 1),
                datetime(today.year, 3 * next_quarter,
                         calendar.monthrange(today.year, 3 * next_quarter)[1], 23, 59, 59, 999999))

    def this_semester():
        today = datetime.now()
        semester = (today.month - 1) // 6 + 1
        return (datetime(today.year, 6 * semester - 5, 1),
                datetime(today.year, 6 * semester,
                         calendar.monthrange(today.year, 6 * semester)[1], 23, 59, 59, 999999))

    def last_semester():
        today = datetime.now()
        semester = (today.month - 1) // 6 + 1
        last_semester = semester - 1
        if last_semester == 0:
            last_semester = 2
        return (datetime(today.year, 6 * last_semester - 5, 1),
                datetime(today.year, 6 * last_semester,
                         calendar.monthrange(today.year, 6 * last_semester)[1], 23, 59, 59, 999999))

    def next_semester():
        today = datetime.now()
        semester = (today.month - 1) // 6 + 1
        next_semester = semester + 1
        if next_semester == 3:
            next_semester = 1
        return (datetime(today.year, 6 * next_semester - 5, 1),
                datetime(today.year, 6 * next_semester,
                         calendar.monthrange(today.year, 6 * next_semester)[1], 23, 59, 59, 999999))

    # endregion

    lookup = {
        "this minute": this_minute,
        "last minute": last_minute,
        "previous minute": last_minute,
        "next minute": next_minute,
        "this hour": this_hour,
        "last hour": last_hour,
        "previous hour": last_hour,
        "next hour": next_hour,

        "today": today,
        "yesterday": yesterday,
        "tomorrow": tomorrow,

        "this year": this_year,
        "last year": last_year,
        "previous year": last_year,
        "next year": next_year,

        "this month": this_month,
        "last month": last_month,
        "previous month": last_month,
        "next month": next_month,

        "this week": this_week,
        "last week": last_week,
        "previous week": last_week,
        "next week": next_week,

        "this quarter": this_quarter,
        "last quarter": last_quarter,
        "previous quarter": last_quarter,
        "next quarter": next_quarter,

        "this semester": this_semester,
        "last semester": last_semester,
        "previous semester": last_semester,
        "next semester": next_semester
    }

    language = language.split("_")[0].lower().strip()
    value = value.strip().lower().replace("_", " ")
    match language:
        case "de":
            # split words if required
            value = split_after_tokens(value, [
                "diese", "dieser", "dieses", "letzte", "letzter", "letztes",
                "nächste", "nächster", "nächstes", "vorherige", "vorheriger", "vorheriges", ])
            # translate to english
            translation_de = {
                "diese minute": "this minute", "letzte minute": "last minute", "nächste minute": "next minute",
                "diese stunde": "this hour", "letzte stunde": "last hour", "nächste stunde": "next hour",
                "heute": "today", "gestern": "yesterday", "morgen": "tomorrow",
                "dieses jahr": "this-year", "letztes jahr": "last year", "nächstes jahr": "next year",
                "dieser monat": "this month", "letzter monat": "last month", "nächster monat": "next month",
                "diese woche": "this week", "letzte woche": "last week", "nächste woche": "next week",
                "dieses quartal": "this quarter", "letztes quartal": "last quarter", "nächstes quartal": "next quarter",
                "dieses semester": "this semester", "letztes semester": "last semester",
                "nächstes semester": "next semester"
            }
            if not value in translation_de:
                return False, None, None
        case "en":
            # split words if required
            value = split_after_tokens(value, ["this", "last", "next"])
        case _:
            # split words if required
            value = split_after_tokens(value, ["this", "last", "next"])

    # lookup english function and return the result
    if value in lookup:
        from_date, to_date = lookup[value]()
        return True, from_date, to_date
    else:
        return False, None, None


def split_after_tokens(value, tokens):
    if " " not in value:
        for token in tokens:
            if value.startswith(token):
                return token + " " + value[len(token):]
    return value
