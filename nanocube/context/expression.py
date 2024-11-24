# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

import ast
import inspect
import math
import operator as op


class ExpressionFunctionLibrary:
    @classmethod
    def mul(cls, a, b):
        return a * b


class Expression:
    # supported operators
    operators = {ast.Add: op.add, ast.Sub: op.sub,
                 ast.Mult: op.mul, ast.Div: op.truediv,
                 ast.Pow: op.pow, ast.Mod: op.mod,
                 ast.And: op.and_, ast.Or: op.or_,
                 ast.Not: op.not_, ast.BitXor: op.xor,
                 ast.USub: op.neg, ast.UAdd: op.add,
                 ast.Gt: op.gt, ast.GtE: op.ge,
                 ast.Lt: op.lt, ast.LtE: op.le,
                 ast.Eq: op.eq, ast.NotEq: op.ne, }

    functions = {"sin": math.sin, "cos": math.cos, "tan": math.tan,
                 "mul": ExpressionFunctionLibrary.mul}

    def __init__(self, expression: str = None):
        self._expression: str = expression
        self._ast_root = None
        self._message: str = ""

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Expression('{self._expression}')"

    @property
    def expression(self):
        return self._expression

    @expression.setter
    def expression(self, value):
        self._expression = value

    @property
    def root(self) -> ast.Expression | None:
        return self._ast_root

    @property
    def message(self):
        return self._message

    def eval(self, expression: str):
        if not isinstance(expression, str):
            raise TypeError("Expression must be a string")
        return self._eval(ast.parse(source=expression, mode='eval').body)

    def parse(self, expression: str | None = None) -> bool:
        if expression is not None:
            self._expression = expression
        try:
            self._ast_root = ast.parse(source=self._expression, mode='eval').body
        except SyntaxError as e:
            self._message = f"Failed to parse expression '{self._expression}'. {e}"
            return False
        return True

    def evaluate(self, resolver):
        return self._eval(self._ast_root, resolver)

    def _eval(self, node, resolver=None):
        if resolver is None:
            raise ValueError("Resolver for expressions must be provided.")
        match node:
            case ast.Constant(value):
                return value
            case ast.BinOp(left, op, right):
                return self.operators[type(op)](self._eval(left, resolver), self._eval(right, resolver))
            case ast.UnaryOp(op, operand):  # e.g., -1
                return self.operators[type(op)](self._eval(operand, resolver))
            case ast.Name():
                # resolve the context
                name = node.id
                context = resolver.resolve(name)
                return context
            case ast.List():
                return [self._eval(e, resolver) for e in node.elts]
            case ast.Tuple():
                return [self._eval(e, resolver) for e in node.elts]
            case ast.Call():
                # get the function to call
                func_name = node.func.id
                func = self.functions[func_name]

                # prepare function arguments
                spec = inspect.getfullargspec(self.functions[func_name])
                func_args_names = [arg for arg in spec.args if arg != "self"]
                func_arg_values = [self._eval(e, resolver) for e in node.args]
                call_dict = dict(zip(func_args_names, func_arg_values))
                for keyword in node.keywords:
                    call_dict[keyword.arg] = self._eval(keyword.value, resolver)

                # call the function
                result = func(**call_dict)
                return result
            case _:
                raise TypeError(node)
