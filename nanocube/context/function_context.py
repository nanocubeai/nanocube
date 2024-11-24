# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

from typing import TYPE_CHECKING

from nanocube.context.context import Context
from nanocube.context.enums import ContextFunction

if TYPE_CHECKING:
    pass


class FunctionContext(Context):
    """
    A context representing a mathematical operation like SUM, MIN, MAX, AVG, etc.
    """
    KEYWORDS = {"SUM", "AVG", "MEDIAN", "MEAN", "MIN", "MAX", "STD", "VAR", "POF",
                "COUNT", "NAN", "AN", "ZERO", "NZERO", "CUSTOM"}

    def __init__(self, parent: Context | None = None, function: ContextFunction | str = ContextFunction.SUM,
                 callable_function=None):
        super().__init__(cube=parent.cube, address=parent.address, parent=parent, row_mask=parent.row_mask,
                         measure=parent.measure, dimension=parent.dimension, resolve=False, filtered=parent.is_filtered)

        if isinstance(function, str):
            try:
                function = ContextFunction[function.upper()]
            except KeyError:
                raise ValueError(f"Unknown function {function}. Supported functions are {FunctionContext.KEYWORDS}")
        self._function:ContextFunction = function
        self._callable_function = callable_function

    def __call__(self, *args, **kwargs):
        if callable(self._callable_function):
            return self._callable_function(*args, **kwargs)
        raise ValueError(f"Function '{self._callable_function}' is not callable or supported.")
