# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

import re
from datetime import datetime, time, timedelta

import dateutil.parser
from dateutil.relativedelta import relativedelta

from nanocube.datespan.date_span import DateSpan
from nanocube.datespan.parser import MIN_YEAR, MAX_YEAR
from nanocube.datespan.parser.errors import EvaluationError, ParsingError
from nanocube.datespan.parser.lexer import Token, TokenType, Lexer
from nanocube.datespan.parser.parser import Parser


class Evaluator:
    """
    The Evaluator class takes the AST produced by the parser_old and computes the actual date spans.
    It handles the logic of converting relative dates and special keywords into concrete date ranges.
    """

    def __init__(self, statements):
        self.statements = statements  # List of statements (AST nodes)
        self.today = datetime.today()  # Current date and time
        self.evaluated_spans = []  # Store evaluated date spans

    def evaluate(self):
        """
        Evaluates all statements and returns a list of date spans for each statement.
        """
        try:
            all_date_spans = []
            for statement in self.statements:
                date_spans = []
                for node in statement:
                    spans = self.evaluate_node(node)
                    date_spans.extend(spans)
                all_date_spans.append(date_spans)
            self.evaluated_spans = all_date_spans
            return all_date_spans
        except Exception as e:
            # Raise an EvaluationError with details
            raise EvaluationError(str(e))

    def evaluate_node(self, node):
        """
        Evaluates a single AST node and returns the corresponding date spans.
        """
        node_type = node.value['type']
        if node_type == 'specific_date':
            return self.evaluate_specific_date(node.value['date'])
        elif node_type == 'relative':
            return self.evaluate_relative(node.value['tokens'])
        elif node_type == 'special':
            return self.evaluate_special(node.value['value'], node=node)
        elif node_type == 'triplet':
            return self.evaluate_triplet(node.value['value'])
        elif node_type == 'months':
            return self.evaluate_months(node.value['tokens'])
        elif node_type == 'days':
            return self.evaluate_days(node.value['tokens'])

        elif node_type == 'range':
            return self.evaluate_range(node.value['start_tokens'], node.value['end_tokens'])
        elif node_type == 'half_bound':
            return self.evaluate_half_bound(node.value['tokens'], node.value['value'])
        elif node_type == 'iterative':
            return self.evaluate_iterative(node.value['tokens'], node.value['period_tokens'])
        else:
            return []

    def evaluate_specific_date(self, date_str):
        """
        Evaluates a specific date string and returns the corresponding date span.
        """

        try:
            try:
                date = dateutil.parser.parse(date_str)
            except ValueError:
                # Parse the date string, allowing fuzzy parsing for complex formats
                date = dateutil.parser.parse(date_str, fuzzy=True, fuzzy_with_tokens=False)
        except ValueError:
            raise EvaluationError(f"Invalid date '{date_str}'.")
        start = date
        end = date
        if date.time() == time(0, 0):
            # If time is not specified, set the span to cover the entire day
            start = datetime.combine(date.date(), time.min)
            end = datetime.combine(date.date(), time.max)
        elif ":" in date_str:
            if "t" in date_str:
                time_str = date_str.split("t")[1]
            else:
                time_str = date_str
            contains_time_zone = time_str.count('+') == 1 or time_str.count('-') == 1
            if contains_time_zone:
                time_str = time_str.split('+')[0].split('-')[0]

            defines_minutes_only = (time_str.count(':') == 1)  # e.g., '12:30'
            if defines_minutes_only:
                # If only hours and minutes are specified, set the span to cover the entire minute
                start = datetime.combine(date.date(), date.time())
                end = start + timedelta(minutes=1, microseconds=-1)
            elif date.microsecond == 0:
                # If seconds are specified, set the span to cover the entire second
                start = datetime.combine(date.date(), date.time())
                end = start + timedelta(seconds=1, microseconds=-1)

        return [(start, end)]

    def evaluate_range(self, start_tokens, end_tokens):
        """
        Evaluates a date range specified by start and end tokens.
        """
        # Evaluate the start date expression
        start_parser = Parser(start_tokens + [Token(TokenType.EOF)])
        try:
            start_ast_nodes = start_parser.parse_statement()
        except ParsingError as e:
            raise EvaluationError(f'Failed to parse start date in range: {e}')
        if not start_ast_nodes:
            raise EvaluationError('Failed to parse start date in range')
        try:
            start_spans = self.evaluate_node(start_ast_nodes[0])
        except EvaluationError as e:
            raise EvaluationError(f'Failed to evaluate start date in range: {e}')
        if not start_spans:
            raise EvaluationError('Failed to evaluate start date in range')
        start_date = start_spans[0][0]

        # Evaluate the end date expression
        end_parser = Parser(end_tokens + [Token(TokenType.EOF)])
        try:
            end_ast_nodes = end_parser.parse_statement()
        except ParsingError as e:
            raise EvaluationError(f'Failed to parse end date in range: {e}')
        if not end_ast_nodes:
            raise EvaluationError('Failed to parse end date in range')
        try:
            end_spans = self.evaluate_node(end_ast_nodes[0])
        except EvaluationError as e:
            raise EvaluationError(f'Failed to evaluate end date in range: {e}')
        if not end_spans:
            raise EvaluationError('Failed to evaluate end date in range')
        end_date = end_spans[0][1]

        # Handle case where only time is specified in end date
        if isinstance(end_date, time):
            end_date = datetime.combine(start_date.date(), end_date)

        return [(start_date, end_date)]

    def evaluate_since(self, tokens):
        """
        Evaluates a 'since' expression, calculating the date range from the specified date/time until now.
        """
        # Parse the date/time expression following 'since'
        parser = Parser(tokens + [Token(TokenType.EOF)])
        try:
            ast_nodes = parser.parse_statement()
        except ParsingError as e:
            raise EvaluationError(f'Failed to parse date in "since" expression: {e}')
        if not ast_nodes:
            raise EvaluationError('Failed to parse date in "since" expression')
        try:
            spans = self.evaluate_node(ast_nodes[0])
        except EvaluationError as e:
            raise EvaluationError(f'Failed to evaluate date in "since" expression: {e}')
        if not spans:
            raise EvaluationError('Failed to evaluate date in "since" expression')
        start_date = spans[0][0]
        end_date = self.today
        return [(start_date, end_date)]

    def evaluate_half_bound(self, tokens, keyword):
        """
        Evaluates a half bounded expression, calculating the date range from or to a specified date/time.
        since - from date to now
        after - from date to date max
        before - from date min to date
        until - from date min to date
        """
        # Parse the date/time expression following 'since', 'after', 'before', or 'until'
        if len(tokens) == 0:
            raise EvaluationError(f"Date of date span missing after "
                                  f"'since', 'after', 'before', or 'until'.")

        parser = Parser(tokens + [Token(TokenType.EOF)])
        try:
            ast_nodes = parser.parse_statement()
        except ParsingError as e:
            raise EvaluationError(
                f"Failed to parse date of date span after 'since', 'after', 'before', or 'until': {e}")
        if not ast_nodes:
            raise EvaluationError(f"Date of date span missing after "
                                  f"'since', 'after', 'before', or 'until'.")

        try:
            spans = self.evaluate_node(ast_nodes[0])
        except EvaluationError as e:
            raise EvaluationError(f"Failed to evaluate date of date span after "
                                  f"'since', 'after', 'before', or 'until': {e}")
        if not spans:
            raise EvaluationError(f"Failed to evaluate date of date span after "
                                  f"'since', 'after', 'before', or 'until'.")

        if keyword == 'since':
            start_date = spans[0][0]
            end_date = self.today
        elif keyword == 'from':
            start_date = spans[0][0]
            end_date = DateSpan.MAX_DATE
        elif keyword == 'after':
            start_date = spans[0][1] + timedelta(microseconds=1)
            end_date = DateSpan.MAX_DATE
        elif keyword in ['before', 'until']:
            start_date = DateSpan.MIN_DATE
            end_date = spans[0][0] - timedelta(microseconds=1)
        else:
            raise EvaluationError(
                f"Failed to evaluate date or datespan. Expected 'since', "
                f"'after', 'before', or 'until' but got '{keyword}'.")
        return [(start_date, end_date)]

    def evaluate_iterative(self, tokens, period_tokens):
        """
        Evaluates an iterative date expression and returns the corresponding date spans.
        """
        # Parse the period expression
        period_parser = Parser(period_tokens + [Token(TokenType.EOF)])
        try:
            period_ast_nodes = period_parser.parse_statement()
        except ParsingError as e:
            raise EvaluationError(f'Failed to parse period in iterative expression: {e}')
        if not period_ast_nodes:
            raise EvaluationError('Failed to parse period in iterative expression')
        try:
            period_spans = self.evaluate_node(period_ast_nodes[0])
        except EvaluationError as e:
            raise EvaluationError(f'Failed to evaluate period in iterative expression: {e}')
        if not period_spans:
            raise EvaluationError('Failed to evaluate period in iterative expression')
        period_start = period_spans[0][0]
        period_end = period_spans[0][1]

        # Determine days of the week
        idx = 0
        ordinals = []
        weekdays = []
        while idx < len(tokens):
            token = tokens[idx]
            if token.type == TokenType.ORDINAL:
                ord_value = self.ordinal_to_int(token.value)
                ordinals.append(ord_value)
            elif token.type == TokenType.IDENTIFIER and token.value in Lexer.DAY_ALIASES.values():
                weekday_num = self.weekday_name_to_num(token.value)
                weekdays.append(weekday_num)
            idx += 1

        if not weekdays:
            raise EvaluationError('No weekdays specified in iterative expression')

        # Generate dates
        date_spans = []
        current_date = period_start
        while current_date <= period_end:
            if current_date.weekday() in weekdays:
                if ordinals:
                    # Check if current date is the nth occurrence in the month
                    for ord_value in ordinals:
                        if self.is_nth_weekday_of_month(current_date, ord_value):
                            start = datetime.combine(current_date.date(), time.min)
                            end = datetime.combine(current_date.date(), time.max)
                            date_spans.append((start, end))
                else:
                    # No ordinal specified, include all matching weekdays
                    start = datetime.combine(current_date.date(), time.min)
                    end = datetime.combine(current_date.date(), time.max)
                    date_spans.append((start, end))
            current_date += timedelta(days=1)
        return date_spans

    def ordinal_to_int(self, ordinal_str):
        """
        Converts an ordinal string like '1st' to an integer.
        """
        return int(re.match(r'(\d+)(?:st|nd|rd|th)', ordinal_str).group(1))

    def weekday_name_to_num(self, weekday_name):
        """
        Converts a weekday name to its corresponding number (Monday=0, Sunday=6).
        """
        weekdays = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6
        }
        return weekdays[weekday_name]

    def is_nth_weekday_of_month(self, date, n):
        """
        Checks if a date is the nth occurrence of its weekday in the month.
        """
        first_day = date.replace(day=1)
        weekday = date.weekday()
        count = 0
        while first_day <= date:
            if first_day.weekday() == weekday:
                count += 1
            if first_day == date:
                return count == n
            first_day += timedelta(days=1)
        return False

    def evaluate_relative(self, tokens):
        """
        Evaluates a relative date expression and returns the corresponding date span.
        """
        idx = 0
        direction = None  # 'last', 'next', 'this', or 'rolling'
        number = None # 1  # Default number if not specified
        unit = None # 'day'  # Default unit
        of_unit = None
        ordinal = None
        while idx < len(tokens):
            token = tokens[idx]
            if token.type == TokenType.IDENTIFIER and token.value in ['past', 'rolling']:
                direction = 'rolling'
            if token.type == TokenType.IDENTIFIER and token.value in ['last', 'previous']:
                direction = 'previous'
            elif token.type == TokenType.IDENTIFIER and token.value == 'next':
                direction = 'next'
            elif token.type == TokenType.IDENTIFIER and token.value == 'this':
                direction = 'this'
            elif token.type == TokenType.IDENTIFIER and token.value == 'of':
                direction = 'of'
            elif token.type == TokenType.NUMBER:
                number = token.value
                if MIN_YEAR <= number <= MAX_YEAR:
                    if direction == 'of':
                        of_unit = 'year'
                    else:
                        unit = 'year'
            elif token.type == TokenType.ORDINAL:
                ordinal = self.ordinal_to_int(token.value)
            elif token.type == TokenType.TIME_UNIT:
                unit = token.value
            elif token.type == TokenType.SPECIAL:
                # Handle rolling periods like 'R3M'
                if token.value.startswith('r') and token.value[-1] in ['d', 'w', 'm', 'y']:
                    direction = 'rolling'
                    number = int(token.value[1:-1])
                    unit_char = token.value[-1]
                    unit_map = {'d': 'day', 'w': 'week', 'm': 'month', 'y': 'year'}
                    unit = unit_map[unit_char]
                else:
                    return self.evaluate_special(token.value)
            idx += 1


        if unit is None:
            unit = 'day'  # Default to day if unit is not specified
        if number is None:
            number = 1  # Default to 1 if number is not specified


        if direction == 'previous':  # incl. 'last'
            return self.calculate_previous(number, unit)
        if direction == 'rolling':  # incl. 'past'
            return self.calculate_rolling(number, unit)
        if direction == 'next':
            return self.calculate_future(number, unit)
        if direction == 'this':
            return self.calculate_this(unit)
        if direction == 'of':
            result = self.calculate_nth_in_period(ordinal, unit)
            start = result[0][0]
            end = result[0][1]
            if of_unit == 'year':
                start = start.replace(year = number)
                end = end.replace(year = number)
            elif of_unit == 'month':
                start = start.replace(month = number)
                end = end.replace(month = number)
            elif of_unit == 'day':
                start = start.replace(day = number)
                end = end.replace(day = number)
            elif of_unit == 'quarter':
                start = start.replace(month= 3 * number - 2)
                end = end.replace(month= 3 * number)

            return [(start, end)]

        if ordinal is not None:
            # Handle expressions like '1st Monday'
            return self.calculate_nth_in_period(ordinal, unit)
        else:  # direction = None
            if unit in ['day', 'week', 'month', 'year', 'quarter']:
                return self.calculate_this(unit)
            return []

    def evaluate_special(self, value, date_spans: list = None, node = None):
        """
        Evaluates a special date expression and returns the corresponding date span.
        """
        if value == 'yesterday':
            return DateSpan.yesterday().to_tuple_list()
        elif value == 'today':
            return DateSpan.today().to_tuple_list()
        elif value == 'tomorrow':
            return DateSpan.tomorrow().to_tuple_list()
        elif value == 'now':
            return DateSpan.now().to_tuple_list()

        elif value == 'ltm':  # last 12 month
            if date_spans:
                date_spans.sort()
                base = date_spans[-1][1]  # latest end date
                span = DateSpan(base).shift_start(years=-1)
                return span.to_tuple_list()
            return DateSpan().ltm.to_tuple_list()
        elif value == 'ytd':
            if date_spans:
                date_spans.sort()
                base = date_spans[-1][1]  # latest end date
                span = DateSpan(DateSpan(base).full_year.start, base)
                return span.to_tuple_list()
            return DateSpan().ytd.to_tuple_list()
        elif value == 'qtd':
            if date_spans:
                date_spans.sort()
                base = date_spans[-1][1]  # latest end date
                span = DateSpan(DateSpan(base).full_quarter.start, base)
                return span.to_tuple_list()
            return DateSpan().qtd.to_tuple_list()
        elif value == 'mtd':
            if date_spans:
                date_spans.sort()
                base = date_spans[-1][1]  # latest end date
                span = DateSpan(DateSpan(base).full_month.start, base)
                return span.to_tuple_list()
            return DateSpan().mtd.to_tuple_list()
        elif value == 'wtd':
            if date_spans:
                date_spans.sort()
                base = date_spans[-1][1]  # latest end date
                span = DateSpan(DateSpan(base).full_week.start, base)
                return span.to_tuple_list()
            return DateSpan().wtd.to_tuple_list()

        # catch the following single words as specials
        elif value == 'week':
            return DateSpan.now().full_week.to_tuple_list()
        elif value == 'month':
            return DateSpan.now().full_month.to_tuple_list()
        elif value == 'year':
            return DateSpan.now().full_year.to_tuple_list()
        elif value == 'quarter':
            return DateSpan.now().full_quarter.to_tuple_list()
        elif value == 'hour':
            return DateSpan.now().full_hour.to_tuple_list()
        elif value == 'minute':
            return DateSpan.now().full_minute.to_tuple_list()
        elif value == 'second':
            return DateSpan.now().full_second.to_tuple_list()
        elif value == 'millisecond':
            return DateSpan.now().full_millisecond.to_tuple_list()


        elif value in ['q1', 'q2', 'q3', 'q4']:
            year = 0
            if node is not None and "tokens" in node.value:
                tokens = node.value["tokens"]
                if tokens and tokens[-1].type == TokenType.NUMBER: # e.g. 'q1 2024'
                    year = tokens[-1].value
                else:  # e.g. 'q1 last year'
                    result = self.evaluate_relative(node.value['tokens'])
                    year = result[0][0].year

            # Specific quarter
            if year == 0:
                year = DateSpan.now().start.year
            quarter = int(value[1])
            month = 3 * (quarter - 1) + 1
            return DateSpan(datetime(year=year, month=month, day=1)).full_quarter.to_tuple_list()
        elif value == 'py':
            return DateSpan.now().shift(years=-1).full_year.to_tuple_list()
        elif value == 'cy':
            return DateSpan.now().full_year.to_tuple_list()
        elif value == 'ny':
            return DateSpan.now().shift(years=1).full_year.to_tuple_list()
        elif value == 'ly':
            return DateSpan.now().shift(years=-1).full_year.to_tuple_list()
        else:
            return []

    def evaluate_triplet(self, triplet: str):

        if not ((triplet[0] in ['r', 'p', 'l', 'n']) and
                (triplet[-1] in ['d', 'w', 'm', 'q', 'y']) and
                (triplet[1:-1].isdigit())):
            raise EvaluationError(f"Invalid triplet '{triplet}'")

        relative = triplet[0]
        number = int(triplet[1:-1])
        unit_char = triplet[-1]
        unit_map = {'d': 'day', 'w': 'week', 'm': 'month', 'q': 'quarter', 'y': 'year'}
        unit = unit_map[unit_char]
        if relative in ['r']:
            return self.calculate_rolling(number, unit)
        elif relative in ['l', 'p']:
            return self.calculate_previous(number, unit)
        elif relative == 'n':
            return self.calculate_future(number, unit)

    def _extract_special_token(self, tokens) -> (list[Token], Token):
        """
        Extracts a special token from the list of tokens if it exists.
        """
        if tokens[-1].type == TokenType.SPECIAL:
            special_token = tokens[-1]
            tokens = tokens[:-1]
            return tokens, special_token
        elif tokens[0].type == TokenType.SPECIAL:
            special_token = tokens[0]
            tokens = tokens[1:]
            return tokens, special_token
        return tokens, None

    def evaluate_months(self, tokens):
        """
        Evaluates a list of months, possibly with a year, and returns the corresponding date spans.
        """
        months = []
        year = 0
        day = 0
        idx = 0
        if not tokens:
            return []

        # check if the last token is a special like 'ytd'
        tokens, special_token = self._extract_special_token(tokens)

        # Check if the last token is a number (year) -> extract the year and remove it
        if tokens and tokens[-1].type == TokenType.NUMBER:
            value = tokens[-1].value
            if DateSpan.MIN_DATE.year <= value <= DateSpan.MAX_DATE.year:
                year = value
                tokens = tokens[:-1]

        # Check if the last token is a punctuation (','), e.g. as in 'June 1st, 2024' -> remove it
        if tokens and tokens[-1].type == TokenType.PUNCTUATION and tokens[-1].value == ',':
            tokens = tokens[:-1]

        #Check if the last token is an ordinal, e.g. as in 'June 1st, 2024' -> get the day of the month and remove it
        if tokens and tokens[-1].type == TokenType.ORDINAL:
            day = self.ordinal_to_int(tokens[-1].value)
            tokens = tokens[:-1]
        elif tokens and tokens[-1].type == TokenType.NUMBER:
            value = tokens[-1].value
            if 1 <= value <= 31:
                day = value
                tokens = tokens[:-1]

        if year == 0:
            year = self.today.year

        while idx < len(tokens):
            token = tokens[idx]
            if token.type == TokenType.IDENTIFIER and token.value in Lexer.MONTH_ALIASES.values():
                month_full_name = token.value
                months.append(month_full_name)
            idx += 1
        date_spans = []
        for month_name in months:
            # Get the month number from the month name
            month_number = datetime.strptime(month_name[:3], '%b').month
            if day == 0:
                from_date = datetime(int(year), month_number, 1)
                to_date = from_date + relativedelta(months=1, days=-1)
            else:
                from_date = datetime(int(year), month_number, day)
                to_date = from_date

            start = datetime.combine(from_date.date(), time.min)
            end = datetime.combine(to_date.date(), time.max)
            date_spans.append((start, end))

        if special_token is not None:
            date_spans = self.evaluate_special(special_token.value, date_spans)

        return date_spans

    def evaluate_days(self, tokens):
        """
        Evaluates a list of days, possibly with a month and year, and returns the corresponding date spans.
        """
        days = []
        # Check if the last token is a number (year)
        if tokens and tokens[-1].type == TokenType.NUMBER:
            year = tokens[-1].value
            tokens = tokens[:-1]  # Remove the year from tokens

        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            if token.type == TokenType.IDENTIFIER and token.value in Lexer.DAY_ALIASES.values():
                day_full_name = token.value
                days.append(day_full_name)
            idx += 1
        date_spans = []

        for day_name in days:
            if day_name == 'monday':
                span = DateSpan().monday
            elif day_name == 'tuesday':
                span = DateSpan().tuesday
            elif day_name == 'wednesday':
                span = DateSpan().wednesday
            elif day_name == 'thursday':
                span = DateSpan().thursday
            elif day_name == 'friday':
                span = DateSpan().friday
            elif day_name == 'saturday':
                span = DateSpan().saturday
            elif day_name == 'sunday':
                span = DateSpan().sunday
            date_spans.append((span.start, span.end))
        return date_spans

    def calculate_rolling(self, number, unit):
        """
        Calculates the rolling period(s) based on the specified number and unit, e.g.
        'rolling 3 months': Refers to a rolling 3-month window, starting from today’s date.
        Note: Rolling and past are synonyms.
        """
        if unit == 'month':  # most used units first
            return DateSpan.now().shift_start(months=-number).to_tuple_list()
        elif unit == 'year':
            return DateSpan.now().shift_start(years=-number).to_tuple_list()
        elif unit == 'quarter':
            return DateSpan.now().shift_start(months=-number * 3).to_tuple_list()
        elif unit == 'week':
            return DateSpan.now().shift(weeks=-1).full_week.shift_start(weeks=number - 1).to_tuple_list()
        elif unit == 'day':
            return DateSpan.now().shift_start(days=-number).to_tuple_list()
        elif unit == 'hour':
            return DateSpan.now().shift_start(hours=-number).to_tuple_list()
        elif unit == 'minute':
            return DateSpan.now().shift_start(minutes=-number).to_tuple_list()
        elif unit == 'second':
            return DateSpan.now().shift_start(seconds=-number).to_tuple_list()
        elif unit == 'millisecond':
            return DateSpan.now().shift_start(microseconds=-number * 1000).to_tuple_list()
        else:
            return []

    def calculate_previous(self, number, unit):
        """
        Calculates the previous period(s) based on the specified number and unit, e.g.
        'previous 3 months': Refers to the full 3 calendar months immediately before the current month.
        Note: Previous and last are synonyms.
        """
        if unit == 'month':  # most used units first
            return DateSpan.today().shift(months=-1).full_month.shift_start(months=-(number - 1)).to_tuple_list()
        elif unit == 'year':
            return DateSpan.today().shift(years=-1).full_year.shift_start(years=-(number - 1)).to_tuple_list()
        elif unit == 'quarter':
            return DateSpan.today().shift(months=-3).full_quarter.shift_start(months=-(number - 1) * 3).to_tuple_list()
        elif unit == 'week':
            return DateSpan.today().shift(weeks=-1).full_week.shift_start(weeks=-(number - 1)).to_tuple_list()
        elif unit == 'day':
            return DateSpan.yesterday().shift_start(days=-(number - 1)).to_tuple_list()
        elif unit == 'hour':
            return DateSpan.now().shift(hours=-1).full_hour.shift_start(hours=-(number - 1)).to_tuple_list()
        elif unit == 'minute':
            return DateSpan.now().shift(minutes=-1).full_minute.shift_start(minutes=-(number - 1)).to_tuple_list()
        elif unit == 'second':
            return DateSpan.now().shift(seconds=-1).full_second.shift_start(seconds=-(number - 1)).to_tuple_list()
        elif unit == 'millisecond':
            return DateSpan.now().shift(microseconds=-1000).full_millisecond.shift_start(
                microseconds=-(number - 1) * 1000).to_tuple_list()
        else:
            return []

    def calculate_future(self, number, unit):
        """
        Calculates a future date range based on the specified number and unit.
        """
        if unit == 'day':
            return DateSpan.today().shift(days=1).shift_end(days=(number - 1)).to_tuple_list()
        elif unit == 'week':
            return DateSpan.today().shift(weeks=1).full_week.shift_end(weeks=(number - 1)).to_tuple_list()
        elif unit == 'month':
            return DateSpan.today().shift(months=1).full_month.shift_end(months=(number - 1)).to_tuple_list()
        elif unit == 'year':
            return DateSpan.today().shift(years=1).full_year.shift_end(years=(number - 1)).to_tuple_list()
        elif unit == 'quarter':
            return DateSpan.today().shift(months=3).full_quarter.shift_end(months=(number - 1) * 3).to_tuple_list()
        elif unit == 'hour':
            return DateSpan.now().shift(hours=1).full_hour.shift_end(hours=number - 1).to_tuple_list()
        elif unit == 'minute':
            return DateSpan.now().shift(minutes=1).full_minute.shift_end(minutes=number - 1).to_tuple_list()
        elif unit == 'second':
            return DateSpan.now().shift(seconds=1).full_second.shift_end(seconds=number - 1).to_tuple_list()
        elif unit == 'millisecond':
            return DateSpan.now().shift(microseconds=1000).full_millisecond.shift_end(
                microseconds=(number - 1) * 1000).to_tuple_list()
        else:
            return []

    def calculate_this(self, unit, ordinal = 0):
        """
        Calculates the date range for the current period specified by the unit (day, week, month, year, quarter).
        """
        base = DateSpan.now()
        if ordinal > 0:
            base = DateSpan(base.ytd.start)
            if unit == 'day':
                base = base.shift(days=ordinal - 1)
            elif unit == 'week':
                base = base.shift(weeks=ordinal - 1)
            elif unit == 'month':
                base = base.shift(months=ordinal - 1)
            elif unit == 'year':
                base = base.shift(years=ordinal - 1)
            elif unit == 'quarter':
                base = base.shift(months=(ordinal - 1) * 3)
            elif unit == 'hour':
                base = base.shift(hours=ordinal - 1)
            elif unit == 'minute':
                base = base.shift(minutes=ordinal - 1)
            elif unit == 'second':
                base = base.shift(seconds=ordinal - 1)

        if unit == 'day':
            return base.full_day.to_tuple_list()
        elif unit == 'week':
            return base.full_week.to_tuple_list()
        elif unit == 'month':
            return base.full_month.to_tuple_list()
        elif unit == 'year':
            return base.full_year.to_tuple_list()
        elif unit == 'quarter':
            return base.full_quarter.to_tuple_list()
        elif unit == 'hour':
            return base.full_hour.to_tuple_list()
        elif unit == 'minute':
            return base.full_minute.to_tuple_list()
        elif unit == 'second':
            return base.full_second.to_tuple_list()
        elif unit == 'millisecond':
            return base.full_millisecond.to_tuple_list()
        else:
            return []

    def calculate_nth_in_period(self, ordinal, unit):
        """
        Calculates the date for the nth weekday in the specified period (e.g., '1st Monday in March').
        """
        period_spans = self.calculate_this(unit=unit, ordinal=ordinal)

        if not period_spans:
            return []
        period_start = period_spans[0][0]
        period_end = period_spans[0][1]


        if unit == 'day':
            # Get the weekday number of today
            weekday_num = ordinal - 1  # self.today.weekday()
            # Use dateutil.relativedelta to find the nth weekday
            nth_weekday_date = period_start + relativedelta(day=1, weekday=weekday_num)

            if period_start <= nth_weekday_date <= period_end:
                start = datetime.combine(nth_weekday_date.date(), time.min)
                end = datetime.combine(nth_weekday_date.date(), time.max)
                return [(start, end)]
            else:
                return []
        else:
            return [(period_start, period_end)]
