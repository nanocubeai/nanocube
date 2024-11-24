# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

import re

from dateutil import parser as dateutil_parser

from nanocube.datespan.parser.errors import ParsingError


class Lexer:
    """
    The Lexer class is responsible for converting the input text into a sequence of tokens.
    It uses regular expressions to match patterns in the text.
    """
    # Aliases for days of the week
    DAY_ALIASES = {
        'mo': 'monday',
        'tu': 'tuesday',
        'we': 'wednesday',
        'th': 'thursday',
        'fr': 'friday',
        'sa': 'saturday',
        'su': 'sunday',
        'mon': 'monday',
        'tue': 'tuesday',
        'tues': 'tuesday',
        'wed': 'wednesday',
        'thu': 'thursday',
        'thur': 'thursday',
        'thurs': 'thursday',
        'fri': 'friday',
        'sat': 'saturday',
        'sun': 'sunday',
        'monday': 'monday',
        'tuesday': 'tuesday',
        'wednesday': 'wednesday',
        'thursday': 'thursday',
        'friday': 'friday',
        'saturday': 'saturday',
        'sunday': 'sunday'
    }

    # Aliases for months
    MONTH_ALIASES = {
        'jan': 'january',
        'feb': 'february',
        'mar': 'march',
        'apr': 'april',
        'may': 'may',
        'jun': 'june',
        'jul': 'july',
        'aug': 'august',
        'sep': 'september',
        'sept': 'september',
        'oct': 'october',
        'nov': 'november',
        'dec': 'december',
        'january': 'january',
        'february': 'february',
        'march': 'march',
        'april': 'april',
        'june': 'june',
        'july': 'july',
        'august': 'august',
        'september': 'september',
        'october': 'october',
        'november': 'november',
        'december': 'december'
    }

    # Aliases for time units
    TIME_UNIT_ALIASES = {
        'd': 'day',
        'day': 'day',
        'days': 'day',

        'week': 'week',
        'weeks': 'week',
        'wk': 'week',
        'wks': 'week',

        'mon': 'month',
        'month': 'month',
        'months': 'month',

        'y': 'year',
        'yr': 'year',
        'yrs': 'year',
        'year': 'year',
        'years': 'year',

        'q': 'quarter',
        'qtr': 'quarter',
        'qrt': 'quarter',  # catch typo
        'qtrs': 'quarter',
        'quarter': 'quarter',
        'quarters': 'quarter',

        'h': 'hour',
        'hr': 'hour',
        'hrs': 'hour',
        'hour': 'hour',
        'hours': 'hour',

        'm': 'minute',
        'min': 'minute',
        'mins': 'minute',
        'minute': 'minute',
        'minutes': 'minute',

        's': 'second',
        'sec': 'second',
        'secs': 'second',
        'second': 'second',
        'seconds': 'second',

        'ms': 'millisecond',
        'millisec': 'millisecond',
        'millisecs': 'millisecond',
        'millisecond': 'millisecond',
        'milliseconds': 'millisecond',

        'μs': 'microsecond',
        'microsec': 'microsecond',
        'microsecs': 'microsecond',
        'microsecond': 'microsecond',
        'microseconds': 'microsecond',
    }

    # Aliases for special words
    SPECIAL_WORDS_ALIASES = {
        'yesterday': 'yesterday',
        'today': 'today',
        'tomorrow': 'tomorrow',
        'now': 'now',

        'ytd': 'ytd',
        'mtd': 'mtd',
        'qtd': 'qtd',
        'wtd': 'wtd',

        'ltm': 'ltm',  # last twelve months

        'py': 'py',  # previous year
        'cy': 'cy',  # current year
        'ny': 'ny',  # next year
        'ly': 'py',  # last year

        'q1': 'q1',
        'q2': 'q2',
        'q3': 'q3',
        'q4': 'q4',

        # 'r3m': 'r3m',
        # 'r4m': 'r4m',
        # 'r6m': 'r6m'
    }

    # Aliases for identifiers
    IDENTIFIER_ALIASES = {
        'last': 'last',

        'previous': 'previous',  # previous = last
        'prev': 'previous',  # prev = last
        'prv': 'previous',  # prev = last

        'past': 'past',
        'rolling': 'rolling',  # rolling = past

        'this': 'this',
        'current': 'this',
        'cur': 'this',
        'actual': 'this',
        'act': 'this',

        'next': 'next',

        'and': 'and',
        'of': 'of',
        'in': 'in',

        'since': 'since',
        'until': 'until',
        'till': 'until',
        'up to': 'upto',  # not yet implemented

        'before': 'before',
        'bef': 'before',
        'bfr': 'before',
        'ante': 'before',

        'after': 'after',
        'aft': 'after',
        'aftr': 'after',
        'post': 'after',

        'from': 'from',
        'frm': 'from',
        'to': 'to',

        'between': 'between',
        'btw': 'between',
        'btwn': 'between',

        'every': 'every',
        'ev': 'every',
        'each': 'every',
    }

    # Include months and days in IDENTIFIER_ALIASES
    IDENTIFIER_ALIASES.update(MONTH_ALIASES)
    IDENTIFIER_ALIASES.update(DAY_ALIASES)

    # Combine all aliases
    ALL_ALIASES = {**MONTH_ALIASES, **DAY_ALIASES, **TIME_UNIT_ALIASES, **SPECIAL_WORDS_ALIASES, **IDENTIFIER_ALIASES}

    # Regular expression for ordinals like '1st', '2nd', '3rd', '4th'
    ORDINAL_PATTERN = r'\b\d+(?:st|nd|rd|th)\b'

    TRIPLET_PATTERN = r'^[rlpn](1000|[1-9][0-9]{0,2})[yqmwd]$'  # r3m, l1q, p2w, n4d

    # Regular expression for times, including optional 'am'/'pm', milliseconds, and microseconds
    TIME_PATTERN = (
        r'\b\d{1,2}:\d{2}(:\d{2})?(\.\d{1,6})?(?:\s?[ap]m)?\b'
    )

    # Build the token specification dynamically
    # First, define the combined patterns

    DATETIME_PATTERN = (
        r'\b\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{1,2}:\d{2}(:\d{2})?(\.\d{1,6})?(?:[+-]\d{2}:\d{2})?(?:\s?[ap]m)?\b'
        r'|'
        r'\b\d{1,2}[./-]\d{1,2}[./-]\d{4}[T ]\d{1,2}:\d{2}(:\d{2})?(\.\d{1,6})?(?:[+-]\d{2}:\d{2})?(?:\s?[ap]m)?\b'
        r'/(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+([+-][0-2]\d:[0-5]\d|Z))|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d([+-][0-2]\d:[0-5]\d|Z))|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d([+-][0-2]\d:[0-5]\d|Z))/'
        r'/(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d)/'
    )

    DATE_PATTERN = (
        r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'
        r'|'
        r'\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b'
    )

    TOKEN_SPECIFICATION = [
        # Recognize datetime strings with optional 'am'/'pm', milliseconds, microseconds, and timezone
        ('DATETIME', DATETIME_PATTERN),
        ('DATE', DATE_PATTERN),  # Date strings
        ('TIME', TIME_PATTERN),  # Time strings
        ('ORDINAL', ORDINAL_PATTERN),  # Ordinal numbers
        ('NUMBER', r'\b\d+\b'),  # Integer numbers
        ('SPECIAL', r'\b(' + '|'.join(re.escape(k) for k in SPECIAL_WORDS_ALIASES.keys()) + r')\b'),  # Special words
        ('TRIPLET', TRIPLET_PATTERN),  # triplet periods, like r3m, r4q, r6y, p2w, n4d
        ('IDENTIFIER', r'\b(' + '|'.join(re.escape(k) for k in IDENTIFIER_ALIASES.keys()) + r')\b'),  # Identifiers
        ('TIME_UNIT', r'\b(' + '|'.join(re.escape(k) for k in TIME_UNIT_ALIASES.keys()) + r')\b'),  # Time units
        ('SEMICOLON', r';'),  # Semicolon to separate statements
        ('PUNCTUATION', r'[,\-]'),  # Commas and hyphens
        ('SKIP', r'\s+'),  # Skip over spaces and tabs
        ('MISMATCH', r'.'),  # Any other character
    ]

    def __init__(self, text):
        """
        Initializes the Lexer with the input text.
        """
        self.text = text.lower()  # Convert input text to lowercase for case-insensitive matching
        self.tokens = []
        self.tokenize()

    def tokenize(self):
        """
        Tokenizes the input text into a list of Token objects.
        """

        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.TOKEN_SPECIFICATION)
        get_token = re.compile(tok_regex, re.IGNORECASE).match
        pos = 0  # Current position in the text
        line = 1
        column = 1

        # remove trailing "." from abbreviations from text
        tokens = []
        for t in str(self.text).split(" "):
            if t.endswith(".") and len(t) > 1:
                if t[-2].isalpha():  # e.g. 'prev.'
                    t = t[:-1]
            tokens.append(t)
        self.text = " ".join(tokens)

        text_length = len(self.text)
        while pos < text_length:
            mo = get_token(self.text, pos)
            if mo is not None:
                kind = mo.lastgroup
                value = mo.group()

                if kind == 'MISMATCH':
                    # let's try if the entire text is a datetime
                    try:
                        result = dateutil_parser.parse(self.text)
                        kind = 'DATETIME'
                        value = self.text
                        token = self.create_token(kind, value, line, column)
                        self.tokens = [token]
                        break

                    except ValueError:
                        pass

                if kind == 'SKIP':
                    # Handle whitespace and update line and column numbers
                    if '\n' in value:
                        line += value.count('\n')
                        column = 1
                    else:
                        column += len(value)
                    pos = mo.end()
                    continue
                elif kind == 'MISMATCH':
                    # get full word for meaningful error message
                    word = str(self.text[pos:]).split(" ")[0]
                    raise ParsingError(f"Unexpected identifier or keyword '{word}'", line, column, word)
                else:
                    token = self.create_token(kind, value, line, column)
                    self.tokens.append(token)
                    # Update position and column
                    pos = mo.end()
                    column += len(value)
            else:
                # No match found; raise an error
                value = self.text[pos]
                raise ParsingError(f"Unexpected character '{value}'", line, column, value)
        self.tokens.append(Token(TokenType.EOF, line=line, column=column))

    def create_token(self, kind, value, line, column):
        """
        Creates a Token object based on the kind and value.
        """
        if kind == 'DATETIME':
            return Token(TokenType.DATETIME, value, line, column)
        elif kind == 'DATE':
            return Token(TokenType.DATE, value, line, column)
        elif kind == 'TIME':
            return Token(TokenType.TIME, value, line, column)
        elif kind == 'NUMBER':
            return Token(TokenType.NUMBER, int(value), line, column)
        elif kind == 'ORDINAL':
            return Token(TokenType.ORDINAL, value, line, column)
        elif kind == 'TIME_UNIT':
            standard_value = self.TIME_UNIT_ALIASES.get(value, value)
            return Token(TokenType.TIME_UNIT, standard_value, line, column)
        elif kind == 'SPECIAL':
            standard_value = self.SPECIAL_WORDS_ALIASES.get(value, value)
            return Token(TokenType.SPECIAL, standard_value, line, column)
        elif kind == 'TRIPLET':
            return Token(TokenType.TRIPLET, value, line, column)
        elif kind == 'IDENTIFIER':
            standard_value = self.IDENTIFIER_ALIASES.get(value, value)
            return Token(TokenType.IDENTIFIER, standard_value, line, column)
        elif kind == 'SEMICOLON':
            return Token(TokenType.SEMICOLON, value, line, column)
        elif kind == 'PUNCTUATION':
            return Token(TokenType.PUNCTUATION, value, line, column)
        else:
            # Treat mismatches as unknown tokens
            return Token(TokenType.UNKNOWN, value, line, column)

    def get_tokens(self):
        """
        Returns the list of tokens.
        """
        return self.tokens

    def __iter__(self):
        """
        Allows iteration over the tokens.
        """
        return iter(self.tokens)


class TokenType:
    """
    Enumeration of possible token types used in the lexer.
    """
    NUMBER = 'NUMBER'
    ORDINAL = 'ORDINAL'  # For ordinal numbers like '1st', '2nd', '3rd', '4th'
    IDENTIFIER = 'IDENTIFIER'
    DATE = 'DATE'
    TIME = 'TIME'
    DATETIME = 'DATETIME'
    TIME_UNIT = 'TIME_UNIT'
    PUNCTUATION = 'PUNCTUATION'
    SPECIAL = 'SPECIAL'
    TRIPLET = 'ROLLING'
    SEMICOLON = 'SEMICOLON'
    EOF = 'EOF'
    START = 'START'
    UNKNOWN = 'UNKNOWN'  # For any unrecognized tokens


class Token:
    """
    A simple Token structure with type, value, and position information.
    """

    def __init__(self, type_, value=None, line=1, column=1):
        self.type = type_
        self.value = value  # The actual value of the token (e.g., 'Monday', '1st')
        self.line = line
        self.column = column

    def __repr__(self):
        return f'Token({self.type}, "{self.value}", Line: {self.line}, Column: {self.column})'
