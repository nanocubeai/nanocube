# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

from __future__ import annotations

import uuid
from datetime import datetime, date, time
from typing import Any, Union

from dateutil.parser import parserinfo

from nanocube.datespan.date_span import DateSpan
from nanocube.datespan.parser.datespanparser import DateSpanParser


class DateSpanSet:
    """
    Represents a sorted set of DateSpan objects. Overlapping DateSpan objects are automatically merged together.
    Provides methods to filter, merge, subtract and compare DateSpan objects as well as to convert them into
    SQL fragments or filter functions for Python, Pandas or others.
    """


    def __init__(self, definition: Any = None, parser_info: parserinfo = None):
        """
        Initializes a new DateSpanSet based on a given set of date span set definition.
        The date span set definition can be a string, a DateSpan, datetime, date or time object or a list of these.

        Arguments:
            definition: (optional) Either a string representing a date or time span expression, a DateSpan, 
            a datetime, date or time object or a list of such arguments.

            parser_info: (optional) A dateutil.parser.parserinfo instance to use for parsing date formats contained
                in date span text. If not defined, the default parserinfo of the dateutil library will be used.

        Errors:
            ValueError: If the language is not supported or the text cannot be parsed.
        """
        self._spans: list[DateSpan] = []
        self._definition = definition
        self._parser_info: parserinfo = parser_info
        self._iter_index = 0

        if definition is not None:
            self._initialize(definition)

    def _initialize(self, definition: Any):
        """
        Initializes the DateSpanSet based on the given definition.
        """
        if definition is not None:
            expressions = []

            # collect available definitions
            if isinstance(definition, (DateSpan, str, datetime, time, date)):
                expressions.append(definition)

            elif isinstance(definition, DateSpanSet):
                self._definition = definition._definition
                expressions.extend(definition._spans)

            elif isinstance(definition, (list, tuple)):
                definitions = []
                for item in definition:
                    if isinstance(item, DateSpan):
                        definitions.append(str(item._arg_start))
                        expressions.append(item)
                    elif isinstance(item, DateSpanSet):
                        definitions.append(str(item._definition))
                        expressions.extend(item._spans)
                    elif isinstance(item, (datetime, time, date)):
                        definitions.append(str(item))
                        expressions.append(item)
                    elif isinstance(item, str):
                        dss = DateSpanSet(item)
                        definitions.append(str(dss._definition))
                        definitions.append(dss._spans)
                    else:
                        raise ValueError(f"Objects of type '{type(item)}' are not supported for DateSpanSet.")
                self._definition = " + ".join(definitions)

            # parse definitions
            try:
                for exp in expressions:
                    if isinstance(exp, DateSpan):
                        self._spans.append(exp)
                    elif isinstance(exp, str):
                        self._parse(exp)
                    elif isinstance(exp, (datetime, date, time)):
                        self._spans.append(DateSpan(exp))
                    else:
                        raise ValueError(f"Objects of type '{type(exp)}' are not supported for DateSpanSet.")
                self._merge_all()
            except ValueError as e:
                raise ValueError(f"Failed to parse '{definition}'. {e}")

    # Magic Methods
    def __iter__(self) -> DateSpanSet:
        self._iter_index = -1
        return self

    def __next__(self) -> DateSpan:  # Python 2: def next(self)
        self._iter_index += 1
        if self._iter_index < len(self._spans):
            return self._spans[self._iter_index]
        raise StopIteration

    def __len__(self):
        return len(self._spans)

    def __getitem__(self, item) -> DateSpan:
        return self._spans[item]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.__class__.__name__}('{self._definition}') := {self._spans}"

    def __add__(self, other) -> DateSpanSet:
        return self.merge(other)

    def __sub__(self, other) -> DateSpanSet:
        return self.subtract(other)

    def __eq__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            if len(self._spans) != len(other._spans):
                return False
            for i, span in enumerate(self._spans):
                if span != other._spans[i]:
                    return False
            return True
        if isinstance(other, DateSpan):
            if len(self._spans) == 1:
                return self._spans[0] == other
            return False
        if isinstance(other, str):
            return self == DateSpanSet(other)
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            return self.start < other.start
        return False

    def __le__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            return self.start <= other.start
        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            return self.start > other.start
        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, DateSpanSet):
            return self.start >= other.start
        return False

    def __contains__(self, item) -> bool:
        test_spans = []
        if isinstance(item, DateSpan):
            test_spans.append(item)
        elif isinstance(item, datetime):
            test_spans.append(DateSpan(item))
        elif isinstance(item, str):
            test_spans.extend(DateSpanSet(item)._spans)
        elif isinstance(item, DateSpanSet):
            test_spans.extend(item._spans)
        else:
            return False  # unsupported type

        # todo: implement more efficient algorithm, check for start and end dates
        for span in self._spans:
            for test_span in test_spans:
                if test_span not in span:
                    return False
        return True

    def __bool__(self) -> bool:
        return len(self._spans) > 0

    def __hash__(self) -> int:
        return hash(tuple(self._spans))

    def __copy__(self) -> DateSpanSet:
        return self.clone()

    # endregion

    @property
    def spans(self) -> list[DateSpan]:
        """Returns the list of DateSpan objects in the DateSpanSet."""
        return self._spans

    @property
    def start(self) -> datetime:
        """Returns the start datetime of the first DateSpan object in the set."""
        if len(self._spans) > 0:
            return self._spans[0].start
        return None

    @property
    def end(self) -> datetime:
        """ Returns the end datetime of the last DateSpan object in the set."""
        if len(self._spans) > 0:
            return self._spans[-1].end
        return None

    def clone(self) -> DateSpanSet:
        """ Returns a deep copy of the DateSpanSet object."""
        dss = DateSpanSet()
        dss._definition = self._definition
        dss._spans = [ds.clone() for ds in self._spans]
        dss._parser_info = self._parser_info
        return dss

    def add(self, other):
        """ Adds a new DateSpan object to the DateSpanSet."""
        merged = self.merge(other)
        self._spans = merged._spans
        self._definition = merged._definition

    def remove(self, other):
        """ Removes a DateSpan object from the DateSpanSet."""
        self._spans = self.intersect(other)._spans

    def shift(self, years: int = 0, months: int = 0, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0,
              microseconds: int = 0, weeks: int = 0) -> DateSpanSet:
        """
        Shifts all contained date spans by the given +/- time delta.
        """
        if not self._spans:
            new_spans: list[DateSpan] = []
            for span in self._spans:
                new_spans.append(span.shift(years=years, months=months, days=days, hours=hours, minutes=minutes,
                                            seconds=seconds, microseconds=microseconds, weeks=weeks))
            return DateSpanSet(new_spans)
        raise ValueError("Failed to shift empty DateSpanSet.")

    # endregion

    # region Class Methods
    @classmethod
    def parse(cls, datespan_text: str, parser_info: parserinfo = None) -> DateSpanSet:
        """
            Creates a new DateSpanSet instance and parses the given text into a set of DateSpan objects.

            Arguments:
                datespan_text: The date span text to parse, e.g. 'last month', 'next 3 days', 'yesterday' or 'Jan 2024'.
                language: (optional) An ISO 639-1 2-digit compliant language code for the language of the text to parse.
                parser_info: (optional) A dateutil.parser.parserinfo instance to use for parsing dates contained
                    datespan_text. If not defined, the default parser of the dateutil library will be used.

            Returns:
                The DateSpanSet instance contain 0 to N DateSpan objects derived from the given text.

            Examples:
                >>> DateSpanSet.parse('last month')  # if today would be in February 2024
                DateSpanSet([DateSpan(datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 31, 23, 59, 59, 999999))])
            """
        return cls(definition=datespan_text, parser_info=parser_info)

    @classmethod
    def try_parse(cls, datespan_text: str, parser_info: parserinfo = None) -> DateSpanSet:
        """
            Creates a new DateSpanSet instance and parses the given text into a set of DateSpan objects. If
            the text cannot be parsed, None is returned.

            Arguments:
                datespan_text: The date span text to parse, e.g. 'last month', 'next 3 days', 'yesterday' or 'Jan 2024'.
                parser_info: (optional) A dateutil.parser.parserinfo instance to use for parsing dates contained
                    datespan_text. If not defined, the default parser of the dateutil library will be used.

            Returns:
                The DateSpanSet instance contain 0 to N DateSpan objects derived from the given text or None.

            Examples:
                >>> a = DateSpanSet.try_parse('last month')  # if today would be in February 2024
                DateSpanSet([DateSpan(datetime.datetime(2024, 1, 1, 0, 0), datetime.datetime(2024, 1, 31, 23, 59, 59, 999999))])
            """
        try:
            dss = cls(definition=datespan_text, parser_info=parser_info)
            return dss
        except ValueError:
            return None

    # endregion

    # region Data Processing Methods And Callables
    def to_sql(self, column: str, line_breaks: bool = False, add_comment: bool = True,
               indentation_in_tabs: int = 0) -> str:
        """
        Converts the date spans representing the DateFilter into an ANSI-SQL compliant SQL fragment to be used
        for the execution of SQL queries.

        Arguments:
            column: The name of the SQL table column to filter.
            line_breaks: (optional) Flag if each date spans should be written in a separate line.
            add_comment: (optional) Flag if a comment with the date span text should be added to the SQL fragment.
                If line_breaks is True, the comment will be added as a separate line, otherwise as an inline comment.
            indentation_in_tabs: (optional) The number of tabs to use for indentation of an SQL fragment.
                Only used if line_breaks is True.

        Returns:
            A string containing an ANSI-SQL compliant fragment to be used in the WHERE clause of an SQL query.
        """
        filters: list[str] = []
        column = column.strip()
        if " " in column and not column[0] in "['\"":
            column = f"[{column}]"
        for i, span in enumerate(self._spans):
            filters.append(f"({column} BETWEEN '{span.start.isoformat()}' AND '{span.end.isoformat()}')")
        comment = f"{len(filters)} filters added from {self.__str__()}" if add_comment else ""
        inline_comment = f" /* {comment} */ " if add_comment else ""
        separate_comment = f"-- {comment}" if add_comment else ""
        if indentation_in_tabs > 0:
            indent = "\t" * indentation_in_tabs
            filters = [f"{indent}{f}" for f in filters]
            separate_comment = f"{indent}{separate_comment}"
        if line_breaks:
            if add_comment:
                return f"{separate_comment}\n" + "OR\n".join(filters)
            return "OR\n".join(filters)
        return " OR ".join(filters) + inline_comment

    def to_function(self, return_sourceCde: bool = False):
        """
        Generate a compiled Python function that can be directly used as a filter function
        within Python, Pandas or other. The lambda function will return True if the input
        datetime is within the date spans of the DateFilter.

        Arguments:
            return_sourceCde: If True, the source code of the function will be returned as a string
                for code reuse. If False, the function will be returned as a callable Python function.

        Examples:
            >>> filter = DateSpanSet("today").to_function()
            >>> print(filter(datetime.now()))
            True

        """
        from types import FunctionType

        # prepare source
        func_name = f"filter_{str(uuid.uuid4()).lower().replace('-', '')}"
        filters: list[str] = [f"def {func_name}(x):", ]
        for i, span in enumerate(self._spans):
            s = span.start
            e = span.end
            if s.hour == 0 and s.minute == 0 and s.second == 0 and s.microsecond == 0 and s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day})"
            elif s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second})"
            else:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second}, microsecond={s.microsecond})"
            end = f"datetime(year={e.year}, month={e.month}, day={e.day}, hour={e.hour}, minute={e.minute}, second={e.second}, microsecond={e.microsecond})"
            filters.append(f"\tif {start} <= x <= {end}:")
            filters.append(f"\t\treturn True")
        filters.append(f"\treturn False")

        source = f"\n".join(filters)
        if return_sourceCde:
            return source
        # compile
        f_code = compile(source, "<bool>", "exec")
        f_func = FunctionType(f_code.co_consts[0], globals(), "func_name")
        return f_func

    def to_lambda(self, return_source_code: bool = False) -> callable:
        """
        Generate a Python lambda function that can be directly used as a filter function
        within Python, Pandas or other. The lambda function will return True if the input
        datetime is within the date spans of the DateFilter.

        Arguments:
            return_source_code: If True, the source code of the lambda function will be returned as a string
                for code reuse. If False, the lambda function will be returned as a callable Python function.

        Examples:
            >>> filter = DateSpanSet("today").to_lambda()
            >>> print(filter(datetime.now()))
            True

        """

        # prepare source
        filters: list[str] = [f"lambda x :", ]
        for i, span in enumerate(self._spans):
            s = span.start
            e = span.end
            if s.hour == 0 and s.minute == 0 and s.second == 0 and s.microsecond == 0 and s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day})"
            elif s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second})"
            else:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second}, microsecond={s.microsecond})"
            end = f"datetime(year={e.year}, month={e.month}, day={e.day}, hour={e.hour}, minute={e.minute}, second={e.second}, microsecond={e.microsecond})"
            if i > 0:
                filters.append(" or ")
            filters.append(f"{start} <= x <= {end}")

        source = f" ".join(filters)
        if return_source_code:
            return source
        # compile
        f_func = eval(source)
        return f_func

    def to_df_lambda(self, return_source_code: bool = False) -> callable:
        """
        Generate a Python lambda function that can be directly applied to Pandas series (column) or
        to a 1d NumPy ndarray as a filter function. This allows the use of NumPy's internal vectorized functions.
        If applied to Pandas, the function will return a boolean Pandas series with the same length as the input series,
        if applied to a NumPy ndarray, the function will return a boolean array with the same length as the input array,
        where True indicates that the input datetime is within the date spans of the DateFilter.

        Arguments:
            return_source_code: If True, the source code of the Numpy lambda function will be returned as a string
                for code reuse. If False, the lambda function will be returned as a callable Python function.

        Examples:
            >>> data = np.array([datetime.now(), datetime.now()])
            >>> filter = DateSpanSet("today").to_df_lambda()
            >>> print(filter(data))
            [True, True]
        """
        # prepare source
        filters: list[str] = [f"lambda x :", ]
        for i, span in enumerate(self._spans):
            s = span.start
            e = span.end
            if s.hour == 0 and s.minute == 0 and s.second == 0 and s.microsecond == 0 and s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day})"
            elif s.microsecond == 0:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second})"
            else:
                start = f"datetime(year={s.year}, month={s.month}, day={s.day}, hour={s.hour}, minute={s.minute}, second={s.second}, microsecond={s.microsecond})"
            end = f"datetime(year={e.year}, month={e.month}, day={e.day}, hour={e.hour}, minute={e.minute}, second={e.second}, microsecond={e.microsecond})"
            if i > 0:
                filters.append(" | ")
            filters.append(f"((x >= {start}) & (x <= {end}))")

        source = f" ".join(filters)
        if return_source_code:
            return source
        # compile
        f_func = eval(source)
        return f_func

    def to_tuples(self) -> list[tuple[datetime, datetime]]:
        """ Returns a list of tuples with start and end dates of all DateSpan objects in the DateSpanSet."""
        return [(ds.start, ds.end) for ds in self._spans]

    def filter(self, data: Any, column: str = None, return_mask: bool = False,
               return_index: bool = False) -> Any:
        """
        Filters the given data object, e.g. a Pandas DataFrame or Series, based on the date spans of the DateSpanSet.

        Arguments:
            data: The data object to filter, e.g. a Pandas DataFrame or Series.
            column: (optional) The name of the column in the DataFrame to filter.
                If None, the data object itself will be filtered.
            return_mask: (optional) If True, a boolean mask will be returned instead of the filtered data.
            return_index: (optional) If True, the index of the filtered data will be returned.

        Returns:
            A filter for the data object, e.g. a boolean Numpy ndarray for direct filtering of Pandas DataFrame or Series.

        Sample:
            >>> df = pd.DataFrame.from_dict({
            ...     "product": ["A", "B", "C", "A", "B", "C"],
            ...     "date": [datetime(2024, 6, 1), datetime(2024, 6, 2),
            ...              datetime(2024, 7, 1), datetime(2024, 7, 2),
            ...              datetime(2024, 12, 1), datetime(2023, 12, 2)],
            ...     "sales": [100, 150, 300, 200, 250, 350]
            ... })
            >>> spans = DateSpanSet("June and December 2024")
            >>> filtered_df = spans.filter(df["date"], return_mask=True)
            >>> print(filtered_df)

        """
        class_name = f"{data.__class__.__module__}.{data.__class__.__qualname__}"
        if class_name == "pandas.core.frame.DataFrame":
            if column is None:
                raise ValueError("A column name must be provided to filter a Pandas DataFrame.")
            mask = self.to_df_lambda()(data[column])
            if return_mask:
                return mask
            elif return_index:
                return data[mask].index.to_numpy()
            return data[mask]

        elif class_name == "pandas.core.series.Series":
            mask = self.to_df_lambda()(data)
            if return_mask:
                return mask
            elif return_index:
                return data[mask].index.to_numpy()
            return data[mask]
        else:
            raise ValueError(f"Objects of type '{class_name}' are not yet supported for filtering.")

    # endregion

    # region Set Operations
    def merge(self, other) -> DateSpanSet:
        """
        Merges the current DateSpanSet with another DateSpanSet, DateSpan or a string representing a data span.
        The resulting DateSpanSet will contain date spans representing all data spans of the current and the other
        DateSpanSet.

        Arguments:
            other: The other DateSpanSet, DateSpan or string to merge with the current DateSpanSet.

        Returns:
            A new DateSpanSet instance containing the merged date spans.
        """
        if isinstance(other, DateSpan):
            return DateSpanSet([self, other])
        if isinstance(other, DateSpanSet):
            return DateSpanSet([self, other])
        if isinstance(other, str):
            return DateSpanSet([self, DateSpanSet(other)])
        raise ValueError(f"Objects of type '{type(other)}' are not supported for DateSpanSet merging.")

    def intersect(self, other) -> DateSpanSet:
        """
        Intersects the current DateSpanSet with another DateSpanSet, DateSpan or a string representing a data span.
        The resulting DateSpanSet will contain data spans that represent the current DataSpanSet minus the date spans
        that are not contained in the other DateSpanSet.

        Arguments:
            other: The other DateSpanSet, DateSpan or string to merge with the current DateSpanSet.

        Returns:
            A new DateSpanSet instance containing the intersected data spans.
        """
        raise NotImplementedError()

    def subtract(self, other) -> DateSpanSet:
        """
        Subtracts a DateSpanSet, DateSpan or a string representing a data span from the current DateSpanSet.
        So, the resulting DateSpanSet will contain data spans that represent the current DataSpanSet minus
        the date spans that are contained in the other DateSpanSet.

        If there is no overlap between the current and the other DateSpanSet, a copy of the current DateSpanSet
        will be returned.

        Arguments:
            other: The other DateSpanSet, DateSpan or string to subtract.

        Returns:
            A new DateSpanSet instance containing reduced DateSpanSet.
        """
        definitions = [str(self._definition)]
        subtracts: list[DateSpan] = []
        if isinstance(other, DateSpan):
            definitions.append(f"({other._arg_start}, {other._arg_end})")
            subtracts.append(other)
        elif isinstance(other, DateSpanSet):
            definitions.append(str(other._definition))
            subtracts.extend(other._spans)
        elif isinstance(other, str):
            dss = DateSpanSet(other)
            definitions.append(str(dss._definition))
            subtracts.extend(dss._spans)
        else:
            raise ValueError(f"Objects of type '{type(other)}' are not supported for DateSpanSet subtraction.")

        result = self.clone()
        final = []
        for sub in subtracts:

            for i, span in enumerate(result._spans):
                if span.overlaps_with(sub):
                    result = span.subtract(sub, allow_split=True)
                    if isinstance(result, DateSpan):
                        if not result.is_undefined:
                            final.append(result)
                    else:
                        final.extend(result)
                else:
                    final.append(span)
        dss = DateSpanSet(final)
        dss._definition = " - ".join(definitions)
        return dss

    # end region

    # region Internal Methods
    def _merge_all(self):
        """
        Merges all overlapping DateSpan objects if applicable.
        """
        if len(self._spans) < 2:
            return  # special case, just one span = nothing to merge

        self._spans.sort()

        current: DateSpan = self._spans[0]
        stack = self._spans[1:]
        stack.reverse()
        merged: list[DateSpan] = []

        while True:
            next: DateSpan = stack.pop()
            if current.can_merge(next):
                current = current.merge(next)
            else:
                merged.append(current)
                current = next
            if not stack:
                merged.append(current)
                break

        self._spans = merged

    def _parse(self, text: str = None):
        """
        Parses the given text into a set of DateSpan objects.
        """
        self._message = None
        self._spans.clear()
        try:
            date_span_parser: DateSpanParser = DateSpanParser(text)
            expressions = date_span_parser.parse()  # todo: inject self.parser_info
            for expr in expressions:
                self._spans.extend([DateSpan(span[0], span[1]) for span in expr])
        except Exception as e:
            self._message = str(e)
            raise ValueError(str(e))
    # endregion
