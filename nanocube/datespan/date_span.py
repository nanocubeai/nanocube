# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

from __future__ import annotations

from datetime import datetime, time, timedelta

from dateutil.relativedelta import MO
from dateutil.relativedelta import relativedelta


class DateSpan:
    """
    Represents a time span with a start and end date. The DateSpan can be used to compare, merge, intersect, subtract
    and shift date spans. The DateSpan can be used to represent a full day, week, month, quarter or year.

    The DateSpan is immutable, all methods that change the DateSpan will return a new DateSpan.
    """
    TIME_EPSILON_MICROSECONDS = 100_000  # 0.1 seconds
    """The time epsilon in microseconds used for detecting overlapping or consecutive date time spans."""

    # Numpy min := '1677-09-22 00:12:43.145225' ... adjusted to the beginning of the next full year
    MIN_DATE = datetime(1678, 1, 1, 0, 0, 0, 0)
    """The Minimum datetime that can be safely represented by a DateSpan. Aligned with the minimum supported datetime of Numpy and Pandas."""
    # Numpy max := '2262-04-11 23:47:16.854775807' ... adjusted to the end of the previous full year
    MAX_DATE = datetime(2261, 12, 31, 23, 59, 59, 999999)
    """The Maximum datetime that can be safely represented by a DateSpan. Aligned with the maximum supported datetime of Numpy and Pandas."""


    def __init__(self, start=None, end=None, message: str = None):
        """
        Initializes a new DateSpan with the given start and end date. If only one date is given, the DateSpan will
        represent a single point in time. If no date is given, the DateSpan will be undefined.

        If `start` and `end` are datetime objects, the DateSpan will be initialized with these datetimes.
        If `start` is larger than `end`, the dates will be automatically swapped.

        If `start` and/or `end` contains arbitrary date span text, the text will be parsed into a DateSpan.
        If both `start` and `end` contain text that refer/resolve to distinct date span, then the resulting
        DateSpan will start at the beginning of the first date span defined by `start` and the end at the end of the
        second date span defined by `end`.

        Raises:
            ValueError: If arguments of the DateSpan are invalid, the DateSpan could not be parsed or the
            parsing of the DateSpan would result in more than one DateSpan. For such cases use the DateSpanSet
            class to parse multipart date spans.
        """
        self._arg_start = start
        self._arg_end = end if end is not None else start
        self._message: str = message

        if isinstance(start, datetime) and isinstance(end, datetime):
            self._start: datetime = start
            self._end: datetime = end if end is not None else start
            self._start, self._end = self._swap()
        elif start is None and end is None:
            self._start: datetime = None
            self._end: datetime = None
        else:
            try:
                self._start, self._end = self._parse(start, end)
            except ValueError as e:
                raise e

    @property
    def message(self) -> str:
        """Returns the message of the DateSpan."""
        return self._message

    @property
    def is_undefined(self) -> bool:
        """Returns True if the DateSpan is undefined."""
        return self._start is None and self._end is None

    @property
    def start(self) -> datetime:
        """Returns the start date of the DateSpan."""
        return self._start

    @start.setter
    def start(self, value: datetime):
        self._start = value
        self._swap()

    @property
    def end(self) -> datetime:
        """Returns the end date of the DateSpan."""
        return self._end

    @end.setter
    def end(self, value: datetime):
        self._end = value
        self._swap()

    def __getitem__(self, item):
        if item == 0:
            return self._start
        if item == 1:
            return self._end
        raise IndexError("Index out of range. DateSpan only supports index 0 and 1.")

    def contains(self, other) -> bool:
        """Returns True if the DateSpan contains the given date, DateSpan or float timestamp."""
        return self.__contains__(other)

    def clone(self) -> DateSpan:
        """Returns a new DateSpan with the same start and end date."""
        return DateSpan(self._start, self._end)

    def overlaps_with(self, other: DateSpan) -> bool:
        """
        Returns True if the DateSpan overlaps with the given DateSpan.
        """
        if self.is_undefined or other.is_undefined:
            return False
        return max(self._start, other._start) <= min(self._end, other._end)

    def consecutive_with(self, other: DateSpan) -> bool:
        """
        Returns True if the DateSpan is consecutive to the given DateSpan, the follow each other without overlap.
        """
        if self.is_undefined or other.is_undefined:
            return False
        if self._start > other._start:
            delta = self._start - other._end
            return timedelta(microseconds=0) <= delta <= timedelta(microseconds=self.TIME_EPSILON_MICROSECONDS)
        delta = other._start - self._end
        return timedelta(microseconds=0) <= delta <= timedelta(microseconds=self.TIME_EPSILON_MICROSECONDS)

    def almost_equals(self, other: DateSpan, epsilon: int = TIME_EPSILON_MICROSECONDS) -> bool:
        """
        Returns True if the DateSpan is almost equal to the given DateSpan.
        """
        start_diff = self._start - other._start
        end_diff = self._end - other._end
        min = timedelta(microseconds=-epsilon)
        max = timedelta(microseconds=epsilon)

        return min <= start_diff <= max and min <= end_diff <= max

    def merge(self, other: DateSpan) -> DateSpan:
        """
        Returns a new DateSpan that is the merge of the DateSpan with the given DateSpan. Merging is only
        possible if the DateSpan overlap or are consecutive.
        """
        if self.is_undefined:
            return other
        if other.is_undefined:
            return self
        if self.overlaps_with(other) or self.consecutive_with(other):
            return DateSpan(min(self._start, other._start), max(self._end, other._end))
        raise ValueError("Cannot merge DateSpans that do not overlap or are not consecutive.")

    def can_merge(self, other: DateSpan) -> bool:
        """
        Returns True if the DateSpan can be merged with the given DateSpan.
        """
        if self.is_undefined or other.is_undefined:
            return True
        return self.overlaps_with(other) or self.consecutive_with(other)

    def intersect(self, other: DateSpan) -> DateSpan:
        """
        Returns a new DateSpan that is the intersection of the DateSpan with the given DateSpan.
        If there is no intersection, an undefined DateSpan is returned.
        """
        if self.is_undefined:
            return other
        if other.is_undefined:
            return self
        if self.overlaps_with(other):
            return DateSpan(max(self._start, other._start), min(self._end, other._end))
        return DateSpan.undefined()

    def subtract(self, other: DateSpan, allow_split: bool = False):
        """
        Returns a new DateSpan that is the subtraction of the DateSpan with the given DateSpan.
        If there is no overlap, the DateSpan will be returned unchanged.
        If the other DateSpan is fully overlapped by the DateSpan, depending on the `allow_split` argument,
        the DateSpan will be split into two DateSpans or an ValueError will be raised, indicating that the
        subtraction can not yield a single DateSpan.

        Arguments:
            allow_split: If True, the DateSpan will be split into two DateSpans if the given
                DateSpan is overlapping. In that case, a tuple of two DateSpans will be returned.
        """
        if self.is_undefined:
            return DateSpan.undefined()
        if other.is_undefined:
            return self
        if other in self:
            # the other is fully overlapped by self
            if self in other:
                # both spans are identical, subtraction will result in an undefined/empty DateSpan
                return DateSpan.undefined()
            if other._start == self._start:  # special case: same start for both spans, cut out the other span
                # we need to full cut out the other span, so we need to go 1 microsecond behind its end
                return DateSpan(other._end + timedelta(microseconds=1), self._end)
            if other._end == self._end:  # special case: same end for both spans, cut out the other span
                # we need to full cut out the other span, so we need to go 1 microsecond before its start
                return DateSpan(self._start, other._start - timedelta(microseconds=1))
            if allow_split:
                return (
                    DateSpan(self._start, other._start - timedelta(microseconds=1)),
                    DateSpan(other._end + timedelta(microseconds=1), self._end)
                )
            raise ValueError("Cannot subtract DateSpan that fully overlaps, without splitting.")

        if not self.overlaps_with(other):
            # no overlapping at all, return self
            return self.clone()

        if other._start < self._start:
            # overlap at the start
            return DateSpan(other._end + timedelta(microseconds=1), self._end)
        # overlap at the end
        return DateSpan(self._start, other._start - timedelta(microseconds=1))

    def with_time(self, time, text: str = None) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the given date and time.
        If text is provided, the DateSpan will be adjusted to the time span specified in the text,
        e.g. "10:23:45" will set the DateSpan to the full second of the given time.
             "10:23" will set the DateSpan to the full minute of the given time.
        """
        start = self._start.replace(hour=time.hour, minute=time.minute, second=time.second,
                                    microsecond=time.microsecond)
        end = self._end.replace(hour=time.hour, minute=time.minute, second=time.second, microsecond=time.microsecond)
        ds = DateSpan(start, end)
        if text is not None:
            parts = text.split(":")
            if len(parts) == 3:
                if "." in parts[2]:
                    return ds
                else:
                    return ds.full_second
            elif len(parts) == 2:
                return ds.full_minute
            elif len(parts) == 1:
                return ds.full_hour
        return ds

    def with_start(self, dt: datetime) -> DateSpan:
        """
        Returns a new DateSpan with the start date set to the given datetime.
        """
        return DateSpan(dt, self._end)

    def with_end(self, dt: datetime) -> DateSpan:
        """
        Returns a new DateSpan with the end date set to the given datetime.
        """
        return DateSpan(self._start, dt)

    def with_date(self, dt: datetime) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the given datetime.
        """
        return DateSpan(dt, dt)

    def with_year(self, year: int) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the given year.
        If the actual DateSpan is longer than a year, the start year will be set to the given year
        and the end year will be adjusted accordingly, e.g. if the DateSpan is from 2024-01-01 to 2025-01-01
        and the year is set to 2023, the DateSpan will be adjusted to 2023-01-01 to 2024-01-01.
        """
        year_diff = self._end.year - self._start.year
        return DateSpan(self._start.replace(year=year), self._end.replace(year=year + year_diff))

    @property
    def full_millisecond(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the respective millisecond(s).
        """
        musec = int(self._start.microsecond // 1000 * 1000)
        return DateSpan(self._start.replace(microsecond=musec),
                        self._end.replace(microsecond=musec + 999))

    @property
    def full_second(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the respective second(s).
        """
        return DateSpan(self._start.replace(microsecond=0),
                        self._end.replace(microsecond=999999))

    @property
    def full_minute(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the respective minute(s).
        """
        return DateSpan(self._start.replace(second=0, microsecond=0),
                        self._end.replace(second=59, microsecond=999999))

    @property
    def full_hour(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the respective hour(s).
        """
        return DateSpan(self._start.replace(minute=0, second=0, microsecond=0),
                        self._end.replace(minute=59, second=59, microsecond=999999))

    @property
    def full_day(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the respective day(s).
        """
        if self.is_undefined:
            return DateSpan(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                            datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999))

        return DateSpan(self._start.replace(hour=0, minute=0, second=0, microsecond=0),
                        self._end.replace(hour=23, minute=59, second=59, microsecond=999999))

    @property
    def full_week(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the respective week(s).
        """
        start = self._start - relativedelta(days=self._start.weekday())
        end = self._end + relativedelta(days=6 - self._end.weekday())
        return DateSpan(start.replace(hour=0, minute=0, second=0, microsecond=0),
                        end.replace(hour=23, minute=59, second=59, microsecond=999999))

    @property
    def full_month(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the respective month(s).
        """
        start = self._start.replace(day=1)
        end = self._end.replace(day=1) + relativedelta(day=31)
        return DateSpan(start.replace(hour=0, minute=0, second=0, microsecond=0),
                        end.replace(hour=23, minute=59, second=59, microsecond=999999))

    @property
    def full_quarter(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the respective quarter(s).
        """
        q_start = (self._start.month - 1) // 3 + 1
        q_end = (self._end.month - 1) // 3 + 1
        m_start = (q_start - 1) * 3 + 1
        m_end = q_end * 3
        start = self._start.replace(month=m_start, day=1)
        end = self._end.replace(month=m_end, day=1) + relativedelta(months=1, days=-1)
        return DateSpan(start.replace(hour=0, minute=0, second=0, microsecond=0),
                        end.replace(hour=23, minute=59, second=59, microsecond=999999))

    @property
    def full_year(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the respective year(s).
        """
        start = self._start.replace(month=1, day=1)
        end = self._end.replace(month=1, day=1) + relativedelta(years=1, days=-1)
        return DateSpan(start.replace(hour=0, minute=0, second=0, microsecond=0),
                        end.replace(hour=23, minute=59, second=59, microsecond=999999))

    @property
    def ltm(self) -> DateSpan:
        """
        Returns a new DateSpan representing the last 12 months relative to the end date of the DateSpan.
        If the DateSpan is undefined, the last 12 months relative to today will be returned.
        """
        if self.is_undefined:
            return DateSpan.today().shift_start(years=-1, days=1)
        ds = DateSpan(self._end, self._end).shift_start(years=-1, days=1)
        return ds

    @property
    def ytd(self) -> DateSpan:
        """
        Returns a new DateSpan with the start set to the beginning of the current DateSpan's start year and the end
        set to the end of the current end date of the DateSpan.
        If the DateSpan is undefined, the beginning of the current year up to today (full day) will be returned.
        """
        if self.is_undefined:
            return DateSpan.today().with_start(DateSpan.today().full_year.start)
        return DateSpan(start=self.with_start(self.full_year.start).start,
                        end=self.end.replace(hour=23, minute=59, second=59, microsecond=999999))

    @property
    def mtd(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the month-to-date.
        """
        if self.is_undefined:
            return DateSpan.today().with_start(DateSpan.today().full_month.start)
        return DateSpan(start=self.with_start(self.full_month.start).start,
                        end=self.end.replace(hour=23, minute=59, second=59, microsecond=999999))

    @property
    def qtd(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the quarter-to-date.
        """
        if self.is_undefined:
            return DateSpan.today().with_start(DateSpan.today().full_quarter.start)
        return DateSpan(start=self.with_start(self.full_quarter.start).start,
                        end=self.end.replace(hour=23, minute=59, second=59, microsecond=999999))

    @property
    def wtd(self) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date set to the beginning and end of the week-to-date.
        """
        if self.is_undefined:
            return DateSpan.today().with_start(DateSpan.today().full_week.start)
        return DateSpan(start=self.with_start(self.full_week.start).start,
                        end=self.end.replace(hour=23, minute=59, second=59, microsecond=999999))

    def _begin_of_day(self, dt: datetime) -> datetime:
        """Returns the beginning of the day for the given datetime."""
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    def _end_of_day(self, dt: datetime) -> datetime:
        """Returns the end of the day for the given datetime."""
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    def _begin_of_month(self, dt: datetime) -> datetime:
        """Returns the beginning of the month for the given datetime."""
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _end_of_month(self, dt: datetime) -> datetime:
        """Returns the end of the month for the given datetime."""
        return dt.replace(day=1, hour=23, minute=59, second=59, microsecond=999999) + relativedelta(months=1, days=-1)

    def _last_day_of_month(self, dt: datetime) -> datetime:
        """Returns the last day of the month for the given datetime."""
        return dt + relativedelta(day=31)

    def _first_day_of_month(self, dt: datetime) -> datetime:
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    @property
    def ends_on_month_end(self) -> bool:
        """
        Returns True if the DateSpan ends on the last day of the month.
        """
        return self._end == self._last_day_of_month(self._end)

    @property
    def begins_on_month_start(self) -> bool:
        """
        Returns True if the DateSpan begins on the first day of the month.
        """
        return self._start == self._first_day_of_month(self._start)

    @property
    def is_full_month(self) -> bool:
        """
        Returns True if the DateSpan represents one or more full months.
        """
        return (self._start == self._begin_of_month(self._start) and
                self._end == self._end_of_month(self._end))

    @property
    def is_full_quarter(self) -> bool:
        """
        Returns True if the DateSpan represents one or more full quarters.
        """
        return (self._start == self._begin_of_month(self._start) and self._start.month % 3 == 1 and
                self._end == self._end_of_month(self._end) and self._end.month % 3 == 0)

    @property
    def is_full_year(self) -> bool:
        """
        Returns True if the DateSpan represents one or more full year.
        """
        return (self._start == self._start.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) and
                self._end == self._end.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999))

    @property
    def is_full_week(self) -> bool:
        """
        Returns True if the DateSpan represents one or more full weeks.
        """
        return (self._start == self._begin_of_day(self._start - timedelta(days=self._start.weekday())) and
                self._end == self._end_of_day(self._end + timedelta(days=6 - self._end.weekday())))

    @property
    def is_full_day(self) -> bool:
        """
        Returns True if the DateSpan represents one or more full days.
        """
        return (self._start == self._begin_of_day(self._start) and
                self._end == self._end_of_day(self._end))

    def replace(self, year: int = None, month: int = None, day: int = None,
                hour: int = None,
                minute: int = None, second: int = None, microsecond: int = None) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date replaced by the given datetime parts.
        """
        if year is None:
            year = self._start.year
        if month is None:
            month = self._start.month
        if day is None:
            day = self._start.day
        if hour is None:
            hour = self._start.hour
        if minute is None:
            minute = self._start.minute
        if second is None:
            second = self._start.second
        if microsecond is None:
            microsecond = self._start.microsecond
        start = self._start.replace(year=year, month=month, day=day, hour=hour, minute=minute,
                                    second=second, microsecond=microsecond)

        if year is None:
            year = self._end.year
        if month is None:
            month = self._end.month
        if day is None:
            day = self._end.day
        if hour is None:
            hour = self._end.hour
        if minute is None:
            minute = self._end.minute
        if second is None:
            second = self._end.second
        if microsecond is None:
            microsecond = self._end.microsecond
        end = self._end.replace(year=year, month=month, day=day, hour=hour, minute=minute,
                                second=second, microsecond=microsecond)
        if self.ends_on_month_end:
            # months and years need to be shifted to proper month end
            end = self._end_of_month(end)

        return DateSpan(start, end)._swap()

    def shift(self, years: int = 0, months: int = 0, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0,
              microseconds: int = 0, weeks: int = 0) -> DateSpan:
        """
        Returns a new DateSpan with the start and end date shifted by the given +/- time delta.
        """
        if self.is_undefined:
            raise ValueError("Cannot shift undefined DateSpan.")
        start = self._start + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes,
                                            seconds=seconds, microseconds=microseconds)

        end = self._end + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes,
                                        seconds=seconds, microseconds=microseconds)
        if weeks:
            start += timedelta(weeks=weeks)
            end += timedelta(weeks=weeks)
        elif days or hours or minutes or seconds or microseconds:
            pass
        elif self.ends_on_month_end:
            # months and years need to be shifted to proper month end
            end = self._end_of_month(end)
        return DateSpan(start, end)

    def shift_start(self, years: int = 0, months: int = 0, days: int = 0, hours: int = 0, minutes: int = 0,
                    seconds: int = 0,
                    microseconds: int = 0, weeks: int = 0) -> DateSpan:
        """
        Shifts the start date of the DateSpan by the given +/- time delta.
        """
        if self.is_undefined:
            raise ValueError("Cannot shift undefined DateSpan.")
        start = self._start + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes,
                                            seconds=seconds, microseconds=microseconds)
        if weeks:
            start += timedelta(weeks=weeks)
        if abs(start - self._end) <= timedelta(microseconds=self.TIME_EPSILON_MICROSECONDS):
            return DateSpan(start, start)

        result = DateSpan(start, self._end)._swap()
        if result.end - result.start < timedelta(microseconds=self.TIME_EPSILON_MICROSECONDS):
            return DateSpan(result.start, result.start)
        return result

    def shift_end(self, years: int = 0, months: int = 0, days: int = 0, hours: int = 0, minutes: int = 0,
                  seconds: int = 0,
                  microseconds: int = 0, weeks: int = 0):
        """
        Shifts the end date of the DateSpan by the given +/- time delta.
        """
        if self.is_undefined:
            raise ValueError("Cannot shift undefined DateSpan.")
        end = self._end + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes,
                                        seconds=seconds, microseconds=microseconds)
        if weeks:
            end += timedelta(weeks=weeks)
        elif days or hours or minutes or seconds or microseconds:
            pass
        elif self.ends_on_month_end:
            # months and years need to be shifted to proper month end
            end = self._end_of_month(end)
        result = DateSpan(self._start, end)._swap()
        if result.end - result.start < timedelta(microseconds=self.TIME_EPSILON_MICROSECONDS):
            return DateSpan(result.start, result.start)
        return result

    def set_start(self, year: int = None, month: int = None, day: int = None,
                  hour: int = None, minute: int = None, second: int = None,
                  microsecond: int = None, ) -> DateSpan:
        """
        Sets the start date of the DateSpan to a specific time or date. Only the given fragments will be set.
        Invalid day values, e.g. set February to 31st, will be automatically adjusted.
        Raises:
            ValueError: If the given datetime fragment is out of range.
        """
        return DateSpan(self._set(self._start, year, month, day, hour, minute, second, microsecond), self._end)

    def set_end(self, year: int = None, month: int = None, day: int = None,
                hour: int = None, minute: int = None, second: int = None,
                microsecond: int = None, ) -> DateSpan:
        """
        Sets the end date of the DateSpan to a specific time or date. Only the given fragments will be set.
        Invalid day values, e.g. set February to 31st, will be automatically adjusted.
        Raises:
            ValueError: If the given datetime fragment is out of range.
        """
        return DateSpan(self._start, self._set(self._end, year, month, day, hour, minute, second, microsecond))

    def set(self, year: int = None, month: int = None, day: int = None,
            hour: int = None, minute: int = None, second: int = None,
            microsecond: int = None, ) -> DateSpan:
        """
        Sets the start and end date of the DateSpan to a specific time or date. Only the given fragments will be set.
        Invalid day values, e.g. set February to 31st, will be automatically adjusted.
        Raises:
            ValueError: If the given datetime fragment is out of range.
        """

        return DateSpan(self._set(self._start, year, month, day, hour, minute, second, microsecond),
                        self._set(self._end, year, month, day, hour, minute, second, microsecond))

    def _set(self, dt: datetime, year: int = None, month: int = None, day: int = None,
             hour: int = None, minute: int = None, second: int = None,
             microsecond: int = None, ) -> datetime:
        """
        Sets a datetime to a specific time or date. Only the given fragments will be set.
        Invalid day values, e.g. set February to 31st, will be automatically
        Raises:
            ValueError: If the given datetime fragment is out of range.
        """
        if dt is None:
            return dt
        if year is not None:
            if not 0 < year < 2100:
                raise ValueError(f"Invalid year value '{year}'.")
            dt = dt.replace(year=year)
        if month is not None:
            if not 0 < month < 13:
                raise ValueError(f"Invalid month value '{month}'.")
            dt = dt.replace(month=month)
        if day is not None:
            if not 0 < day < 32:
                raise ValueError(f"Invalid day value '{day}'.")
            last_day = DateSpan(self._start).full_month._end.day
            if day > last_day:
                day = last_day
            dt = dt.replace(day=day)
        if hour is not None:
            if not 0 <= hour < 24:
                raise ValueError(f"Invalid hour value '{hour}'.")
            dt = dt.replace(hour=hour)
        if minute is not None:
            if not 0 <= minute < 60:
                raise ValueError(f"Invalid minute value '{minute}'.")
            dt = dt.replace(minute=minute)
        if second is not None:
            if not 0 <= second < 60:
                raise ValueError(f"Invalid second value '{second}'.")
            dt = dt.replace(second=second)
        if microsecond is not None:
            if not 0 <= microsecond < 1000000:
                raise ValueError(f"Invalid microsecond value '{microsecond}'.")
            dt = dt.replace(microsecond=microsecond)
        return dt

    @property
    def timedelta(self) -> timedelta:
        """
        Returns the time delta between the start and end date of the DateSpan. Same as `duration`.
        """
        return self._end - self._start

    @property
    def duration(self) -> float:
        """
        Returns the duration of the DateSpan in days as a float. Decimal digits represent fractions of a day.
        """
        return (self._end - self._start).total_seconds() / 86400.0

    def to_tuple(self) -> tuple[datetime, datetime]:
        """
        Returns the start and end date of the DateSpan as a tuple.
        """
        return self._start, self._end

    def to_tuple_list(self) -> list[tuple[datetime, datetime]]:
        """
        Returns the start and end date of the DateSpan as a list containing a single tuple.
        """
        return [(self._start, self._end), ]

    # region Static Days, Month and other calculations
    @classmethod
    def max(cls) -> DateSpan:
        """
        Returns the maximum possible DateSpan ranging from MIN_DATE to MAX_DATE.
        """
        return DateSpan(cls.MIN_DATE, cls.MAX_DATE)

    @classmethod
    def now(cls) -> DateSpan:
        """Returns a new DateSpan with the start and end date set to the current date and time."""
        now = datetime.now()
        return DateSpan(now, now)

    @classmethod
    def today(cls) -> DateSpan:
        """Returns a new DateSpan with the start and end date set to the current date."""
        return DateSpan.now().full_day

    @classmethod
    def yesterday(cls) -> DateSpan:
        """Returns a new DateSpan with the start and end date set to yesterday."""
        return DateSpan.now().shift(days=-1).full_day

    @classmethod
    def tomorrow(cls) -> DateSpan:
        """Returns a new DateSpan with the start and end date set to tomorrow."""
        return DateSpan.now().shift(days=1).full_day

    @classmethod
    def undefined(cls) -> DateSpan:
        """Returns an undefined DateSpan. Same as `span = DateSpan()`."""
        return DateSpan(None, None)

    @classmethod
    def _monday(cls, base: datetime = None, offset_weeks: int = 0, offset_years: int = 0, offset_months: int = 0,
                offset_days: int = 0) -> DateSpan:
        # Monday is 0 and Sunday is 6
        if base is None:
            base = datetime.now()
        dtv = base + relativedelta(weekday=MO(-1), years=offset_years,
                                   months=offset_months, days=offset_days, weeks=offset_weeks)
        return DateSpan(dtv).full_day

    @property
    def monday(self):
        """
        Returns the Monday relative to the week of the start date time of the DateSpan.
        If the DateSpan is undefined, the current week's Monday will be returned.
        """
        return self._monday(base=self._start)

    @property
    def tuesday(self):
        """
        Returns the Tuesday relative to the week of the start date time of the DateSpan.
        If the DateSpan is undefined, the current week's Tuesday will be returned.
        """
        return self._monday(base=self._start).shift(days=1)

    @property
    def wednesday(self):
        """
        Returns the Wednesday relative to the week of the start date time of the DateSpan.
        If the DateSpan is undefined, the current week's Wednesday will be returned.
        """
        return self._monday(base=self._start).shift(days=2)

    @property
    def thursday(self):
        """
        Returns the Thursday relative to the week of the start date time of the DateSpan.
        If the DateSpan is undefined, the current week's Thursday will be returned.
        """
        return self._monday(base=self._start).shift(days=3)

    @property
    def friday(self):
        """
        Returns the Friday relative to the week of the start date time of the DateSpan.
        If the DateSpan is undefined, the current week's Friday will be returned.
        """
        return self._monday(base=self._start).shift(days=4)

    @property
    def saturday(self):
        """
        Returns the Saturday relative to the week of the start date time of the DateSpan.
        If the DateSpan is undefined, the current week's Saturday will be returned.
        """
        return self._monday(base=self._start).shift(days=5)

    @property
    def sunday(self):
        """
        Returns the Sunday relative to the week of the start date time of the DateSpan.
        If the DateSpan is undefined, the current week's Sunday will be returned.
        """
        return self._monday(base=self._start).shift(days=6)

    @property
    def january(self):
        """
        Returns a full month DateSpan for January relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's January will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=1).full_month
        return self._start.replace(month=1).full_month

    @property
    def february(self):
        """
        Returns a full month DateSpan for February relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's February will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=2).full_month
        return self._start.replace(month=2).full_month

    @property
    def march(self):
        """
        Returns a full month DateSpan for March relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's March will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=3).full_month
        return self._start.replace(month=3).full_month

    @property
    def april(self):
        """
        Returns a full month DateSpan for April relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's April will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=4).full_month
        return self._start.replace(month=4).full_month

    @property
    def may(self):
        """
        Returns a full month DateSpan for May relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's May will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=5).full_month
        return self._start.replace(month=5).full_month

    @property
    def june(self):
        """
        Returns a full month DateSpan for June relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's June will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=6).full_month
        return self._start.replace(month=6).full_month

    @property
    def july(self):
        """
        Returns a full month DateSpan for July relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's July will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=7).full_month
        return self._start.replace(month=7).full_month

    @property
    def august(self):
        """
        Returns a full month DateSpan for August relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's August will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=8).full_month
        return self._start.replace(month=8).full_month

    @property
    def september(self):
        """
        Returns a full month DateSpan for September relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's September will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=9).full_month
        return self._start.replace(month=9).full_month

    @property
    def october(self):
        """
        Returns a full month DateSpan for October relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's October will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=10).full_month
        return self._start.replace(month=10).full_month

    @property
    def november(self):
        """
        Returns a full month DateSpan for November relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's November will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=11).full_month
        return self._start.replace(month=11).full_month

    @property
    def december(self):
        """
        Returns a full month DateSpan for December relative to the start date time of the DateSpan.
        If the DateSpan is undefined, the current year's December will be returned.
        """
        if self.is_undefined:
            return DateSpan.now().replace(month=12).full_month
        return self._start.replace(month=12).full_month

    # endregion

    # region magic methods
    def __add__(self, other):
        if isinstance(other, timedelta):
            return DateSpan(self._start + other, self._end + other)
        if isinstance(other, DateSpan):
            return self.merge(other)
        raise ValueError(f"Add object of type '{type(other).__name__}' "
                         f"to 'DateSpan' object is not supported. "
                         f"Only types timedelta and DateSpan are supported. "
                         f"Use 'shift', 'set' or 'merge' methods instead.")

    def __sub__(self, other):
        if isinstance(other, timedelta):
            return DateSpan(self._start - other, self._end - other)
        if isinstance(other, DateSpan):
            return self.subtract(other)
        raise ValueError(f"Subtract object of type '{type(other).__name__}' "
                         f"from 'DateSpan' object is not supported. "
                         f"Only types timedelta and DateSpan are supported. "
                         f"Use 'shift', 'set' or 'intersect' methods instead.")

    def __contains__(self, item):
        if isinstance(item, datetime):
            return self._start <= item <= self._end
        if isinstance(item, DateSpan):
            return self._start <= item.start <= item.end <= self._end
        if isinstance(item, float):
            item = datetime.fromtimestamp(item)
            return self.start <= item <= self.end
        return False

    def __bool__(self):
        return not (self._start is None and self._end is None)

    def __str__(self):
        if self.is_undefined:
            return "DateSpan(undefined)"

        start = f"'{self._arg_start}'" if isinstance(self._arg_start, str) else str(self._arg_start)
        end = f"'{self._arg_end}'" if isinstance(self._arg_end, str) else str(self._arg_end)
        return f"DateSpan({start}, {end})"  # -> ('start': {self._start}, 'end': {self._end})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is None:
            return self._start is None and self._end is None
        if isinstance(other, DateSpan):
            if self.is_undefined and other.is_undefined:
                return True
            if self.is_undefined or other.is_undefined:
                return False

            if self.start.tzinfo is not None and other.start.tzinfo is not None:
                return self.start == other.start and self.end == other.end
            if self.start.tzinfo is None and other.start.tzinfo is None:
                return self.start == other.start and self.end == other.end
            return self.start.replace(tzinfo=None) == other.start.replace(tzinfo=None) and self.end.replace(
                tzinfo=None) == other.end.replace(tzinfo=None)
        if isinstance(other, datetime):
            return self.start == other and self.end == other
        if isinstance(other, tuple):
            return self.start == other[0] and self.end == other[1]
        if isinstance(other, float):
            other = datetime.fromtimestamp(other)
            return self.start == other and self.end == other
        return False

    def __gt__(self, other):
        if isinstance(other, DateSpan):
            return self.start > other.start and self.end > other.end
        if isinstance(other, datetime):
            return self.start > other and self.end > other
        if isinstance(other, tuple):
            return self.start > other[0] and self.end > other[1]
        if isinstance(other, float):
            other = datetime.fromtimestamp(other)
            return self.start > other and self.end > other
        return False

    def __ge__(self, other):
        if isinstance(other, DateSpan):
            return self.start >= other.start and self.end >= other.end
        if isinstance(other, datetime):
            return self.start >= other and self.end >= other
        if isinstance(other, tuple):
            return self.start >= other[0] and self.end >= other[1]
        if isinstance(other, float):
            other = datetime.fromtimestamp(other)
            return self.start >= other and self.end >= other
        return False

    def __lt__(self, other):
        if isinstance(other, DateSpan):
            return self.start < other.start and self.end < other.end
        if isinstance(other, datetime):
            return self.start < other and self.end < other
        if isinstance(other, tuple):
            return self.start < other[0] and self.end < other[1]
        if isinstance(other, float):
            other = datetime.fromtimestamp(other)
            return self.start < other and self.end < other
        return False

    def __le__(self, other):
        if isinstance(other, DateSpan):
            return self.start <= other.start and self.end <= other.end
        if isinstance(other, datetime):
            return self.start <= other and self.end <= other
        if isinstance(other, tuple):
            return self.start <= other[0] and self.end <= other[1]
        if isinstance(other, float):
            other = datetime.fromtimestamp(other)
            return self.start <= other and self.end <= other
        return False

    def __hash__(self):
        return hash((self._start, self._end))

    # endregion

    # region private methods
    def _swap(self) -> DateSpan:
        """Swap start and end date if start is greater than end."""
        if self._start is None or self._end is None:
            return self

        if self._start > self._end:
            tmp = self._start
            self._start = self._end
            self._end = tmp
        return self

    def _parse(self, start, end=None) -> (datetime, datetime):
        """Parse a date span string."""
        if end is None:
            expected_spans = 1
            text = start
        else:
            expected_spans = 2
            text = f"{start}; {end}"  # merge start and end into a single date span statement

        self._message = None
        try:
            from nanocube.datespan.parser.datespanparser import DateSpanParser  # overcome circular import
            date_span_parser: DateSpanParser = DateSpanParser(text)
            expressions = date_span_parser.parse()  # todo: inject self.parser_info
            if len(expressions) != expected_spans:
                raise ValueError(f"The date span expression '{text}' resolves to "
                                 f"more than just a single date span. "
                                 f"Use 'DateSpanSet('{text}')' to parse multi-part date spans.")
            if expected_spans == 2:
                start = expressions[0][0][0]
                end = expressions[1][0][1]
            else:
                start = expressions[0][0][0]
                end = expressions[0][0][1]

            return start, end
        except Exception as e:
            self._message = str(e)
            raise ValueError(str(e))
