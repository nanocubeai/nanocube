# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
from __future__ import annotations

from enum import IntEnum


class BooleanOperation(IntEnum):
    """Supported boolean operations for Context objects for filtering purposes."""
    AND = 1
    """Logical AND operation. The result will contain only the rows contained in both context objects."""
    OR = 2
    """Logical OR operation. The result will contain the rows of both context objects."""
    XOR = 3
    """Logical XOR operation. The result will contain the rows of the two context objects except the rows contained in both."""
    NOT = 4
    """Logical NOT operation. Unary Operation, the result will contain the rows not contained in the context object."""


class ContextAllocation(IntEnum):
    """
    Supported Allocation functions for value write back in a cube.
    """
    DISTRIBUTE = 1
    """Distributes a new value to all affected records based on the current distribution of values."""
    SET = 2
    """Sets the new value to all affected records, independent of the current values."""
    DELTA = 3
    """Adds the new value to all affected records. Nan values are treated as zero values."""
    MULTIPLY = 4
    """Multiplies all affected records with the new value."""
    ZERO = 5
    """Sets all affected values/records to zero. Dependent on the measure type, the value is set to either (int) 0 or (float) 0.0."""
    NAN = 6
    """Sets all affected values/records to NaN."""
    DEL = 7
    """Deletes all affected records from the Pandas dataframe."""
    CUSTOM = 8
    """Custom allocation function, defined by the user."""


class ContextFunction(IntEnum):
    """
    Supported aggregation functions for data.
    """
    SUM = 1
    """Sum of all values in the current context."""
    AVG = 2
    """Average of all values in the current context."""
    MEAN = 2
    """Average of all values in the current context."""
    MEDIAN = 3
    """Median of all values/rows in the current context."""
    MIN = 4
    """Minimum of all values/rows in the current context."""
    MAX = 5
    """Maximum of all values/rows in the current context."""
    STD = 6
    """Standard deviation of all values/rows in the current context."""
    VAR = 7
    """Variance of all values/rows in the current context."""
    POF = 8
    """Percentage of the first value in the current context."""

    # returning an integer
    COUNT = 9
    """Number of values/rows in the current context."""
    NAN = 10
    """Number of NaN values/rows in the current context."""
    AN = 11
    """Number of non-NaN values/rows in the current context."""
    ZERO = 12
    """Number of zero values/rows in the current context."""
    NZERO = 13
    """Number of non-zero values/rows in the current context."""
    CUSTOM = 14
    """Custom aggregation function, defined by the user."""


    @staticmethod
    def is_count_function(function_type: int) -> bool:
        """Returns True if the function type represents one of the
        counting function types `COUNT`, `NAN`, `AN`, `ZERO` or `NZERO`."""
        return function_type >= ContextFunction.COUNT


