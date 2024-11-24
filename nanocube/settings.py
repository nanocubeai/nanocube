# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from enum import IntEnum

EAGER_CACHING_THRESHOLD: int = 256  # upper dimension cardinality limit (# of members in dimension) for EAGER caching

class CachingStrategy(IntEnum):
    """
    Caching strategy for faster data access to cubes. Defines if, when and how data should be cached.

    Recommended value for most use cases is `LAZY` caching (caching on first access). For smaller datasets or datasets
    with low cardinality dimensions, `EAGER` caching (pre caching of low cardinality dimensions, other on access) can
    be beneficial.

    `FULL` caching (pre caching of all dimensions) is recommended only for long-living and smaller, low cardinality
    datasets where fast access is crucial, e.g. using CubedPandas for data access through a web service.
    `FULL` caching should be avoided for large or short-living datasets due to the implied memory and run-time penalty.
    `NONE` caching is recommended for large datasets, when memory is limited, when the dataset is not used frequently
    or when the performance is not crucial.
    """
    NONE = 0
    LAZY = 1
    EAGER = 2
    FULL = 3

    def __str__(self):
        return f'{self.__class__.__name__}.{self.name}'

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.lower()
            if value in dir(cls):
                return cls[value]
        return cls.LAZY  # default

    @classmethod
    def from_any(cls, value):
        if isinstance(value, bool):
            return CachingStrategy.EAGER if value else CachingStrategy.NONE
        if isinstance(value, str):
            caching = value.upper().strip()
            if caching in CachingStrategy.__members__:
                return CachingStrategy[caching]
            else:
                # calls the `_missing_` method, returns the default caching value
                return CachingStrategy(caching)
        else:
            return CachingStrategy(str(value).upper().strip())



class CubeSettings:

    def __init__(self):
        self._list_delimiter = ","
        self._auto_whitespace: bool = True
        self._read_only: bool = True
        self._convert_values_to_python_data_types: bool = True

        self._auto_rounding: bool = False
        self._populate_members: bool = False
        self._ignore_member_key_errors: bool = False
        self._ignore_case: bool = False
        self._ignore_key_errors: bool = False
        self._return_none_for_non_existing_cells: bool = False
        self._eager_evaluation: bool = True
        self._debug_mode: bool = False

        self._caching_strategy: CachingStrategy = CachingStrategy.LAZY
        self._caching_threshold: int = EAGER_CACHING_THRESHOLD


    @property
    def list_delimiter(self):
        return self._list_delimiter

    @list_delimiter.setter
    def list_delimiter(self, value):
        self._list_delimiter = value


    @property
    def auto_whitespace(self):
        """
        Returns:
            `True`, if all measure-, dimension- and member-names containing whitespace
            can be written using underscores instead of a whitespace to support Python
            attribute naming conventions for dynamic access, e.g., `cdf.List_Price` will
            return the value of the measure column named 'List Price'.

            `False`, if the names must be written exactly as they are in the cube/dataframe,
            `cdf.List_Price` will return the value of the measure column named 'List_Price'

            Default is `True`.
        """
        return self._auto_whitespace

    @auto_whitespace.setter
    def auto_whitespace(self, value):
        """
        Returns:
            `True`, if all measure-, dimension- and member-names containing whitespace
            can be written using underscores instead of a whitespace to support Python
            attribute naming conventions for dynamic access, e.g., `cdf.List_Price` will
            return the value of the measure column named 'List Price'.

            `False`, if the names must be written exactly as they are in the cube/dataframe,
            `cdf.List_Price` will return the value of the measure column named 'List_Price'

            Default is `True`.
        """
        self._auto_whitespace = value

    @property
    def read_only(self) -> bool:
        """
        Returns:
            True if the Cube is read-only, otherwise False.
        """
        return self._read_only

    @read_only.setter
    def read_only(self, value: bool):
        """
        Sets the read-only status of the Cube.
        """
        self._read_only = value

    @property
    def convert_values_to_python_data_types(self) -> bool:
        """
        Returns:
            True if all values in the cube are converted to Python data types, otherwise False.
        """
        return self._convert_values_to_python_data_types

    @convert_values_to_python_data_types.setter
    def convert_values_to_python_data_types(self, value: bool):
        """
        Defines if all values in the cube are converted to Python data types.
        """
        self._convert_values_to_python_data_types = value


    @property
    def ignore_member_key_errors(self) -> bool:
        """
        Returns:
            True if the Cube is ignoring member key errors, otherwise False.
        """
        return self._ignore_member_key_errors

    @ignore_member_key_errors.setter
    def ignore_member_key_errors(self, value: bool):
        """
        Sets the member key error handling of the Cube.
        """
        self._ignore_member_key_errors = value

    @property
    def return_none_for_non_existing_cells(self) -> bool:
        """
        Returns:
            True if the Cube is returning None for non-existing cells, otherwise False.
        """
        return self._return_none_for_non_existing_cells

    @return_none_for_non_existing_cells.setter
    def return_none_for_non_existing_cells(self, value: bool):
        """
        Sets the return value for non-existing cells.
        """
        self._return_none_for_non_existing_cells = value


    @property
    def ignore_case(self) -> bool:
        """
        Returns:
            True if the Cube is ignoring case, otherwise False.
        """
        return self._ignore_case

    @ignore_case.setter
    def ignore_case(self, value: bool):
        """
        Sets the case sensitivity of the Cube.
        """
        self._ignore_case = value

    @property
    def ignore_key_errors(self) -> bool:
        """
        Returns:
            True if the Cube is ignoring key errors, otherwise False.
        """
        return self._ignore_key_errors

    @ignore_key_errors.setter
    def ignore_key_errors(self, value: bool):
        """
        Sets the key error handling of the Cube.
        """
        self._ignore_key_errors = value

    @property
    def eager_evaluation(self) -> bool:
        """
        Returns:
            Returns `True` if the cube will evaluate the context eagerly, i.e. when the context is created.
            Eager evaluation is recommended for most use cases, as it simplifies debugging and error handling.
            Returns `False` if the cube will evaluate the context lazily, i.e. only when the value of a context
            is accessed/requested.
        """
        return self._eager_evaluation

    @eager_evaluation.setter
    def eager_evaluation(self, value: bool):
        """
        Sets the evaluation strategy for the cube.
        """
        self._eager_evaluation = value

    @property
    def caching_threshold(self) -> int:
        """
        caching_threshold:
            The threshold as 'number of members' for EAGER caching only. If the number of
            distinct members in a dimension is below this threshold, the dimension will be cached
            eargerly, if caching is set to CacheStrategy.EAGER or CacheStrategy.FULL. Above this
            threshold, the dimension will be cached lazily.
            Default value is `EAGER_CACHING_THRESHOLD`, equivalent to max. 256 unique members per dimension.
        """
        return self._caching_threshold

    @caching_threshold.setter
    def caching_threshold(self, value: int):
        """
        Sets the threshold for EAGER caching.
        """
        self._caching_threshold = value



    @property
    def caching_strategy(self) -> CachingStrategy:
        """
        Returns:
            The caching strategy for the cube.
        """
        return self._caching_strategy

    @caching_strategy.setter
    def caching_strategy(self, value: CachingStrategy):
        """
        Sets the caching strategy for the cube.
        """
        self._caching_strategy = value

    @property
    def populate_members(self) -> bool:
        """
        Returns:
            True if the Cube is populating members, otherwise False.
        """
        return self._populate_members

    @populate_members.setter
    def populate_members(self, value: bool):
        """
        Sets the member population strategy for the cube.
        """
        self._populate_members = value

    @property
    def debug_mode(self) -> bool:
        """
        Returns:
            True if the Cube is in debug mode, otherwise False.
        """
        return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, value: bool):
        """
        Sets the debug mode for the cube.
        """
        self._debug_mode = value

    # disabled for now
    # @property
    # def auto_rounding(self) -> bool:
    #     """
    #     Sets the auto rounding strategy for the cube.
    #     """
    #     return self._auto_rounding
    #
    # @auto_rounding.setter
    # def auto_rounding(self, value: bool):
    #     """
    #     Sets the auto rounding strategy for the cube.
    #     """
    #     self._auto_rounding = value