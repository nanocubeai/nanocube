# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

from nanocube.datespan.parser.errors import ParsingError
from nanocube.datespan.parser.lexer import Token, TokenType, Lexer


class ASTNode:
    """
    Base class for nodes in the abstract syntax tree.
    """
    pass


class DateSpanNode(ASTNode):
    """
    Represents a date span node in the AST, which can be a specific date, relative period, or range.
    """

    def __init__(self, value):
        self.value = value  # Dictionary containing details about the date span

    def __str__(self):
        return f"DateSpanNode({self.value})"


class Parser:
    """
    The Parser class processes the list of tokens and builds an abstract syntax tree (AST).
    It follows the grammar rules to parse date expressions.
    """

    def __init__(self, tokens, text=None):
        self.tokens = tokens
        self.text = text
        self.pos = 0  # Current position in the token list
        self.current_token = self.tokens[self.pos]
        self.statements = [] if text is None else text.split(';')
        self.ast = None  # Store the abstract syntax tree

    def __str__(self):
        return f"Parser('{self.text}')"

    def __repr__(self):
        return f"Parser('{self.text}')"

    @property
    def previous_token(self):
        """
        Returns the previous token in the list.
        """
        return self.tokens[self.pos - 1] if self.pos > 0 else Token(TokenType.START, line=0, column=0)

    @property
    def next_token(self):
        """ Returns the next token in the list. """
        return self.tokens[self.pos + 1] if self.pos < len(self.tokens) - 1 else Token(TokenType.EOF, line=0, column=0)

    def eat(self, token_type):
        """
        Consumes the current token if it matches the expected token type.
        """
        if self.current_token.type == token_type:
            self.advance()
        else:
            raise ParsingError(
                f"Unexpected token {self.current_token.value!r}. Expected token type '{token_type}'",
                self.current_token.line,
                self.current_token.column,
                self.current_token.value
            )

    def advance(self):
        """
        Advances to the next token.
        """
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = Token(TokenType.EOF, line=self.current_token.line, column=self.current_token.column)

    def parse(self):
        """
        Parses the tokens and returns a list of statements (each statement is a list of DateSpan nodes).
        """
        try:
            statements = []
            while self.current_token.type != TokenType.EOF:
                date_spans = self.parse_statement()
                statements.append(date_spans)
                if self.current_token.type == TokenType.SEMICOLON:
                    self.eat(TokenType.SEMICOLON)
                else:
                    break  # No more statements

            # add remaining tokens
            if self.pos < len(self.tokens) - 1:
                node = statements[-1][-1].value
                if 'tokens' not in node:
                    node['tokens'] = []
                node["tokens"].extend(self.tokens[self.pos:-1])

            self.ast = statements
            return statements
        except Exception as e:
            # Raise a ParsingError with position information
            raise ParsingError(str(e), self.current_token.line, self.current_token.column, self.current_token.value)

    def parse_statement(self):
        """
        Parses a single statement, which may contain multiple date spans separated by punctuation or 'and'.
        """
        date_spans = []
        while self.current_token.type != TokenType.EOF and self.current_token.type != TokenType.SEMICOLON:
            node = self.date_span()
            date_spans.append(node)
            if self.current_token.type == TokenType.PUNCTUATION or \
                    (self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and'):
                self.eat(self.current_token.type)  # Consume ',' or 'and'
            else:
                if self.current_token.type == TokenType.TIME:
                    node = self.date_span()
                    date_spans.append(node)
                break  # End of date spans in this statement
        return date_spans

    def date_span(self):
        """
        Parses a date span, which can be a specific date, relative date, range, or special period.
        """
        if self.current_token.type == TokenType.IDENTIFIER:
            if self.current_token.value == 'every':
                return self.iterative_date_span()
            elif self.current_token.value in ['last', 'next', 'past', 'previous', 'rolling', 'this']:
                return self.relative_date_span()
            elif self.current_token.value in ['after', 'before', 'since', 'until']:
                return self.half_bound_date_span()
            elif self.current_token.value in ['between', 'from']:
                return self.date_range()
            elif self.current_token.value in Lexer.MONTH_ALIASES.values():
                return self.month_date_span()
            elif self.current_token.value in Lexer.DAY_ALIASES.values():
                return self.day_date_span()
            # elif self.current_token.value in Lexer.TIME_UNIT_ALIASES.values():
            #     return self.month_date_span()
            else:
                raise ParsingError(
                    f'Unexpected identifier {self.current_token.value!r}',
                    self.current_token.line,
                    self.current_token.column,
                    self.current_token.value
                )

        elif self.current_token.type == TokenType.SPECIAL:
            return self.special_date_span()
        elif self.current_token.type == TokenType.TRIPLET:
            return self.triplet_date_span()
        elif self.current_token.type in [TokenType.DATE, TokenType.DATETIME]:
            return self.specific_date_span()
        elif self.current_token.type in [TokenType.TIME]:
            return self.specific_time_span()
        elif self.current_token.type == TokenType.NUMBER or self.current_token.type == TokenType.ORDINAL:
            return self.relative_date_span()
        elif self.current_token.type == TokenType.TIME_UNIT:
            if len(self.tokens) <= 2 and self.tokens[-1].type == TokenType.EOF:
                # single word month, quarter, year, week, hour, minute, second or millisecond, handle as specials
                self.current_token.type = TokenType.SPECIAL
                return self.special_date_span()
            return self.relative_date_span()
        else:
            raise ParsingError(
                f'Unexpected token {self.current_token.value!r} of type {self.current_token.type}',
                self.current_token.line,
                self.current_token.column,
                self.current_token.value
            )

    def iterative_date_span(self):
        """
        Parses an iterative date span, such as 'every Mon, Tue, Wed in this month' or 'every 1st Monday of YTD'.
        """
        self.eat(TokenType.IDENTIFIER)  # Consume 'every'
        tokens = []
        # Optionally consume ordinal and weekdays
        while True:
            if self.current_token.type == TokenType.ORDINAL:
                tokens.append(self.current_token)
                self.eat(TokenType.ORDINAL)
            elif self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in Lexer.DAY_ALIASES.values():
                tokens.append(self.current_token)
                self.eat(TokenType.IDENTIFIER)
                if self.current_token.type == TokenType.PUNCTUATION:
                    self.eat(TokenType.PUNCTUATION)
                elif self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and':
                    self.eat(TokenType.IDENTIFIER)
            elif self.current_token.type == TokenType.TIME_UNIT and self.current_token.value in Lexer.TIME_UNIT_ALIASES.values():
                tokens.append(self.current_token)
                self.eat(TokenType.TIME_UNIT)
            else:
                break  # No more ordinals or weekdays

        # Expect 'in' or 'of'
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in ['in', 'of']:
            self.eat(TokenType.IDENTIFIER)
        else:
            raise ParsingError(
                f"Expected 'in' or 'of', got {self.current_token}",
                self.current_token.line,
                self.current_token.column,
                self.current_token.value
            )
        # Collect period tokens
        period_tokens = []
        while self.current_token.type != TokenType.EOF and \
                not (self.current_token.type == TokenType.PUNCTUATION or
                     self.current_token.type == TokenType.SEMICOLON):
            period_tokens.append(self.current_token)
            self.eat(self.current_token.type)
        return DateSpanNode({'type': 'iterative', 'tokens': tokens, 'period_tokens': period_tokens})

    def specific_date_span(self):
        """
        Parses a specific date, possibly with time, and returns a DateSpan node.
        """
        date_value = self.current_token.value
        token_type = self.current_token.type
        self.eat(token_type)
        # Optionally consume a time after the date
        if self.current_token.type == TokenType.TIME:
            time_value = self.current_token.value
            self.eat(TokenType.TIME)
            date_value += ' ' + time_value  # Combine date and time
        return DateSpanNode({'type': 'specific_date', 'date': date_value})

    def specific_time_span(self):
        """
        Parses a specific date, possibly with time, and returns a DateSpan node.
        """
        time_value = self.current_token.value
        token_type = self.current_token.type
        self.eat(token_type)
        return DateSpanNode({'type': 'specific_date', 'date': time_value})

    def date_range(self):
        """
        Parses a date range expression, such as 'from ... to ...' or 'between ... and ...'.
        """
        token = self.current_token
        self.eat(TokenType.IDENTIFIER)  # Consume 'from' or 'between'
        # Parse the start date expression
        start_tokens = []
        while self.current_token.type != TokenType.EOF and \
                not (self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in ['and', 'to']):
            start_tokens.append(self.current_token)
            self.eat(self.current_token.type)
        # Consume 'and' or 'to'
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in ['and', 'to']:
            self.eat(TokenType.IDENTIFIER)
        else:
            if token.value == 'from':
                # special case, 'from' without 'to' or 'and'
                return DateSpanNode({'type': 'half_bound', 'tokens': start_tokens, 'value': token.value})
            raise ParsingError(
                f"Expected 'and' or 'to', got '{self.current_token.value!r}'",
                self.current_token.line,
                self.current_token.column,
                self.current_token.value
            )
        # Parse the end date expression
        end_tokens = []
        while self.current_token.type != TokenType.EOF and \
                not (self.current_token.type == TokenType.PUNCTUATION or
                     self.current_token.type == TokenType.SEMICOLON or
                     (self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and')):
            end_tokens.append(self.current_token)
            self.eat(self.current_token.type)
        return DateSpanNode({'type': 'range', 'start_tokens': start_tokens, 'end_tokens': end_tokens})

    def since_date_span(self):
        """
        Parses a 'since' date expression, such as 'since August 2024'.
        """
        self.eat(TokenType.IDENTIFIER)  # Consume 'since'
        tokens = []
        while self.current_token.type != TokenType.EOF and \
                not (self.current_token.type == TokenType.PUNCTUATION or
                     self.current_token.type == TokenType.SEMICOLON):
            tokens.append(self.current_token)
            self.eat(self.current_token.type)
        return DateSpanNode({'type': 'since', 'tokens': tokens})

    def half_bound_date_span(self):
        """
        Parses date time spans with a one side bound like 'since', 'before', 'after' date expression,
        e.g. as in 'since August 2024', 'after Friday' or 'before 2024'.
        """
        token = self.current_token
        self.eat(TokenType.IDENTIFIER)  # Consume half bound keyword
        tokens = []
        while self.current_token.type != TokenType.EOF and \
                not (self.current_token.type == TokenType.PUNCTUATION or
                     self.current_token.type == TokenType.SEMICOLON):
            tokens.append(self.current_token)
            self.eat(self.current_token.type)
        return DateSpanNode({'type': 'half_bound', 'tokens': tokens, 'value': token.value})

    def relative_date_span(self):
        """
        Parses a relative date span, such as 'last week' or 'next 3 months'.
        """
        tokens = []
        while True:

            if self.current_token.type in [TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.ORDINAL,
                                          TokenType.TIME_UNIT, TokenType.SPECIAL]:
                tokens.append(self.current_token)
                self.eat(self.current_token.type)
            else:
                break
        return DateSpanNode({'type': 'relative', 'tokens': tokens})

    def special_date_span(self):
        """
        Parses a special date span, such as 'today' or 'ytd'.
        """
        token = self.current_token
        self.eat(TokenType.SPECIAL)
        return DateSpanNode({'type': 'special', 'value': token.value})

    def triplet_date_span(self):
        """
        Parses a special date span, such as 'today' or 'ytd'.
        """
        token = self.current_token
        self.eat(TokenType.TRIPLET)
        return DateSpanNode({'type': 'triplet', 'value': token.value})

    def month_date_span(self):
        """
        Parses a date span that specifies months, such as 'Jan, Feb and August of 2024'.
        """
        tokens = []
        while self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in Lexer.MONTH_ALIASES.values():
            tokens.append(self.current_token)
            self.eat(TokenType.IDENTIFIER)
            if self.current_token.type == TokenType.PUNCTUATION:
                self.eat(TokenType.PUNCTUATION)  # Consume comma or hyphen
            elif self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and':
                self.eat(TokenType.IDENTIFIER)

        # Optionally consume 'of' and a year
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'of':
            self.eat(TokenType.IDENTIFIER)
        if self.current_token.type == TokenType.NUMBER:
            tokens.append(self.current_token)  # Append a year, month or day number
            self.eat(TokenType.NUMBER)
            # check for punctuation ',' as in 'Jan 15, 2024'
            if self.current_token.type == TokenType.PUNCTUATION:
                if self.next_token.type in [TokenType.NUMBER, TokenType.ORDINAL]:
                    tokens.append(self.current_token)
                    self.eat(TokenType.PUNCTUATION)
                    tokens.append(self.current_token)
                    self.eat(self.current_token.type)


        # optional eat trailing time tokens
        if self.current_token.type == TokenType.TIME_UNIT:
            tokens.append(self.current_token)
            self.eat(TokenType.TIME_UNIT)

        return DateSpanNode({'type': 'months', 'tokens': tokens})

    def day_date_span(self):
        """
        Parses a date span that specifies months, such as 'Monday, Tuesday and Friday of this week'.
        """
        # method added by TZ
        tokens = []
        while self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in Lexer.DAY_ALIASES.values():
            tokens.append(self.current_token)
            self.eat(TokenType.IDENTIFIER)
            if self.current_token.type == TokenType.PUNCTUATION:
                self.eat(TokenType.PUNCTUATION)  # Consume comma or hyphen
            elif self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'and':
                self.eat(TokenType.IDENTIFIER)

        # Optionally consume 'of' and a year
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value == 'of':
            self.eat(TokenType.IDENTIFIER)
        if self.current_token.type == TokenType.NUMBER:
            tokens.append(self.current_token)  # Append the year
            self.eat(TokenType.NUMBER)
        return DateSpanNode({'type': 'days', 'tokens': tokens})
