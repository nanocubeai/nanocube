# datespan - Copyright (c)2024, Thomas Zeutschler, MIT license

from nanocube.datespan.parser.errors import ParsingError
from nanocube.datespan.parser.evaluator import Evaluator
from nanocube.datespan.parser.lexer import Lexer
from nanocube.datespan.parser.parser import Parser


class DateSpanParser:
    """
    The DateSpanParser class serves as the main interface. It takes an input string,
    tokenizes it, parses the tokens into an AST, and evaluates the AST to produce date spans.
    """

    def __init__(self, text):
        self.text = str(text).strip()
        self.lexer = None
        self.parser = None
        self.evaluator = None

    def parse(self) -> list:
        """
        Parses the input text and evaluates the date spans.
        """
        if not self.text:
            raise ParsingError('Input text cannot be empty.', line=1, column=0, token_value='')

        try:
            self.lexer = Lexer(self.text)

            self.parser = Parser(self.lexer.tokens, self.text)
            statements = self.parser.parse()

            self.evaluator = Evaluator(statements)
            self.evaluator.evaluate()

            return self.evaluator.evaluated_spans

        except Exception as e:
            raise e

    @property
    def tokens(self):
        """
        Returns the list of tokens from the lexer.
        """
        return self.lexer.tokens if self.lexer else []

    @property
    def parse_tree(self):
        """
        Returns the abstract syntax tree from the parser_old.
        """
        return self.parser.ast if self.parser else None

    @property
    def date_spans(self):
        """
        Returns the evaluated date spans from the evaluator.
        """
        return self.evaluator.evaluated_spans if self.evaluator else []
