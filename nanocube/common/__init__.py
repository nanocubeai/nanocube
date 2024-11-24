# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
from __future__ import annotations

from decimal import Decimal
import pandas as pd

from nanocube.settings import CachingStrategy


def cubed(df: pd.DataFrame, schema=None,
          exclude: str | list | tuple | None = None,
          caching: CachingStrategy = CachingStrategy.LAZY,
          read_only: bool = True):
    """
    Wraps a Pandas dataframes into a cube to provide convenient multi-dimensional access
    to the underlying dataframe for easy aggregation, filtering, slicing, reporting and
    data manipulation and write back.

    Args:
        df:
            The Pandas dataframe to be wrapped into the CubedPandas `Cube` object.

        schema:
            (optional) A schema that defines the dimensions and measures of the Cube. If not provided, a
            default schema, treating all numerical columns will as measures, all other columns as dimensions,
            will be automatically inferred from the dataframe. If this behaviour is not desired, a valid
            schema must be provided. Default value is `None`.

        exclude:
            (optional) Defines the columns that should be excluded from the cube if no schema is provied.
            If a column is excluded, it will not be part of the schema and can not be accessed through the cube.
            Excluded columns will be ignored during schema inference. Default value is `None`.

        caching:
            (optional) A caching strategy to be applied for accessing the cube. recommended
            value for almost all use cases is `CachingStrategy.LAZY`, which caches
            dimension members on first access. Caching can be beneficial for performance, but
            may also consume more memory. To cache all dimension members eagerly (on
            initialization of the cube), set this parameter to `CachingStrategy.EAGER`.
            Please refer to the documentation of 'CachingStrategy' for more information.
            Default value is `CachingStrategy.LAZY`.


        read_only:
            (optional) Defines if write backs to the underlying dataframe are permitted.
            If read_only is set to `True`, write back attempts will raise an `PermissionError`.
            If read_only is set to `False`, write backs are permitted and will be pushed back
            to the underlying dataframe.
            Default value is `True`.

    Returns:
        A new Cube object that wraps the dataframe.

    Raises:
        PermissionError:
            If writeback is attempted on a read-only Cube.

        ValueError:
            If the schema is not valid or does not match the dataframe or if invalid
            dimension, member, measure or address agruments are provided.

    Examples:
        >>> df = pd.value([{"product": ["A", "B", "C"]}, {"value": [1, 2, 3]}])
        >>> cdf = cubed(df)
        >>> cdf["product:B"]
        2
    """
    from nanocube.cube import Cube
    return Cube(df=df, schema=schema, exclude=exclude,
                caching=caching,
                read_only=read_only)


def pythonize(name: str, lowered: bool = False) -> str:
    """
    Converts a string into a valid Python variable name by replacing all invalid characters with underscores.

    The first character must be a letter or an underscore, all following characters can be letters, digits or
    underscores.

    Args:
        name:
            The string to be converted into a valid Python variable name.
        lowered:
            If True, the resulting variable name will be lowercased. Default is False.

    Returns:
        A valid Python variable name.

    Examples:
        >>> pythonize("Hello World")
        'Hello_World'
    """
    # Remove all invalid characters from the string
    name = "".join([c if c.isalnum() or c == "_" else "_" for c in name])
    # Replace all occurrences of "__" with "_"
    while "__" in name:
        name = name.replace("__", "_")
    # Remove leading and trailing "_" from the string
    if name.startswith("_"):
        name = name[1:]
    if name.endswith("_"):
        name = name[:-1]
    # Lowercase the string if lowered is True
    if lowered:
        name = name.lower()
    return name


def smart_round(value: float | int, precision: int = 6, min_digits: int = 2) -> float | int:
    """
    Rounds a numerical value to an 'appropriate' number of digits.
    
    Args:
        value:
            The value to be rounded.
        
        precision:
            The number of digits of the value to be preserved. Default is 6.
            For a value of 0.000123456789 and min_precision = 6, the result will be 0.000123456.
            For a value of 123456.789 and min_precision = 6, the result will be 123456 + the
            number of decimal digits as defined by argument `min_digits`.
        
        min_digits:
            The minimum number of decimal digits to be displayed. Default is 2.
    Returns:
        The rounded value.
    """
    if isinstance(value, int):
        return value

    adj_exp = Decimal(value).adjusted()
    a = 1
    if adj_exp <= 0:
        return round(value, abs(adj_exp) + precision - 1)
    else:
        return round(value, max(min_digits, precision - adj_exp - 1))
