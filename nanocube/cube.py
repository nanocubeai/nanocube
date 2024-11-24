# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

import sys
from typing import Any

import pandas as pd

from nanocube.ambiguities import Ambiguities
from nanocube.context import Context, CubeContext, FilterContext
from nanocube.schema import DimensionCollection
from nanocube.schema import MeasureCollection
from nanocube.schema import Schema
from nanocube.settings import CachingStrategy
from nanocube.settings import CubeSettings


class Cube:
    """
    Wraps a Pandas dataframes into a cube to provide convenient multi-dimensional access
    to the underlying dataframe for easy aggregation, filtering, slicing, reporting and
    data manipulation and write back.
    A schema, that defines the dimensions and measures of the Cube, can either be
    inferred automatically from the underlying dataframe (default) or defined explicitly.
    """

    def __init__(self, df: pd.DataFrame,
                 schema=None,
                 exclude: str | list | tuple | None = None,
                 read_only: bool = True,
                 ignore_member_key_errors: bool = True,
                 ignore_case: bool = False,
                 ignore_key_errors: bool = True,
                 caching: CachingStrategy = CachingStrategy.LAZY
                 ):
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

            read_only:
                (optional) Defines if write backs to the underlying dataframe are permitted.
                If read_only is set to `True`, write back attempts will raise an `PermissionError`.
                If read_only is set to `False`, write backs are permitted and will be pushed back
                to the underlying dataframe.
                Default value is `True`.

            ignore_case:
                (optional) FEATURE NOT YET RELEASED - If set to `True`, the case of member names will be ignored,
                'Apple' and 'apple' will be treated as the same member. If set to `False`, member names are
                case-sensitive and 'Apple' and 'apple' will be treated as different members.
                Default value is `False`.

            ignore_key_errors:
                (optional) If set to `True`, key errors for members of dimensions will be ignored and
                cell values will return 0.0 or `None` if no matching record exists. If set to `False`,
                key errors will be raised as exceptions when accessing cell values for non-existing members.
                Default value is `True`.

            caching:
                (optional) A caching strategy to be applied for accessing the cube. recommended
                value for almost all use cases is `CachingStrategy.LAZY`, which caches
                dimension members on first access. Caching can be beneficial for performance, but
                may also consume more memory. To cache all dimension members on
                initialization of the cube, set caching to `CachingStrategy.EAGER`.
                Please refer to the documentation of 'CachingStrategy' for more information.
                Default value is `CachingStrategy.LAZY`.

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
        self._settings = CubeSettings()
        if not read_only is None:
            self._settings.read_only = read_only
            self._settings.ignore_member_key_errors = ignore_member_key_errors
            self._settings.ignore_case = ignore_case
            self._settings.ignore_key_errors = ignore_key_errors


        self._convert_values_to_python_data_types: bool = True
        self._df: pd.DataFrame = df
        self._exclude: str | list | tuple | None = exclude
        self._caching: CachingStrategy = caching
        self._member_cache: dict = {}
        self._runs_in_jupyter = Cube._runs_in_jupyter()

        # get or prepare the cube schema and setup dimensions and measures
        if schema is None:
            schema = Schema(df).infer_schema(exclude=self._exclude)
        else:
            schema = Schema(df, schema)
        self._schema: Schema = schema
        self._dimensions: DimensionCollection = schema.dimensions
        self._measures: MeasureCollection = schema.measures
        self._ambiguities: Ambiguities | None = None

        # warm up cache, if required
        if self._caching >= CachingStrategy.EAGER:
            self._warm_up_cache()

    # region Properties

    @property
    def settings(self) -> CubeSettings:
        """
        Returns:
            The settings of the Cube.
        """
        return self._settings

    @property
    def ambiguities(self) -> Ambiguities:
        """
        Returns:
            An Ambiguities object that provides information about ambiguous data types in the underlying dataframe.
        """
        if self._ambiguities is None:
            self._ambiguities = Ambiguities(self._df, self._dimensions, self._measures)
        return self._ambiguities

    # @property
    # def linked_cubes(self) -> CubeLinks:
    #     """
    #     Returns:
    #         A list of linked cubes that are linked to this cube.
    #     """
    #     # todo: implement a proper linked cubes collection object
    #     return self._cube_links

    @property
    def schema(self) -> Schema:
        """
        Returns:
            The Schema of the Cube which defines the dimensions and measures of the Cube.
        """
        return self._schema

    @property
    def df(self) -> pd.DataFrame:
        """Returns:
        The underlying Pandas dataframe of the Cube.
        """
        return self._df

    def __len__(self):
        """
        Returns:
            The number of records in the underlying dataframe of the Cube.
        """
        return len(self._df)

    def _warm_up_cache(self):
        """Warms up the cache of the Cube, if required."""
        if self._caching >= CachingStrategy.EAGER:
            for dimension in self._schema.dimensions:
                dimension._cache_warm_up()
    # endregion

    # region Data Access Methods

    # Note: deprecated in favor of the __getattr__ and __getitem__ methods
    # @property
    # def context(self) -> Context:
    #     context = CubeContext(self)
    #     return context

    def __getattr__(self, name) -> Context | CubeContext:
        """
        Dynamically resolves dimensions, measure or member from the cube.
        This enables a more natural access to the cube data using the Python dot notation.

        If the name is not a valid Python identifier and contains special characters or whitespaces
        or start with numbers, then the `slicer` method needs to be used to resolve the name,
        e.g., if `12 data %` is the name of a column or value in a dataframe, then `cube["12 data %"]`
        needs to be used to return the dimension, measure or column.

        Args:
            name: Existing Name of a dimension, member or measure in the cube.

        Returns:
            A Cell object that represents the cube data related to the address.

        Samples:
            >>> cdf = cubed(df)
            >>> cdf.Online.Apple.cost
            50
        """
        if name == "_ipython_canary_method_should_not_exist": # pragma: no cover
            raise AttributeError("cubedpandas")

        context = CubeContext(self, dynamic_attribute=True)

        if str(name).endswith("_"):
            name = str(name)[:-1]
            context = context[name]
            context = FilterContext(context)
            return context

        return context[name]

    def __getitem__(self, address: Any) -> Context:
        """
        Returns a cell of the cube for a given address.
        Args:
            address:
                A valid cube address.
                Please refer the documentation for further details.

        Returns:
            A Cell object that represents the cube data related to the address.

        Raises:
            ValueError:
                If the address is not valid or can not be resolved.
        """
        context = CubeContext(self)
        return context[address]

    def __setitem__(self, address, value):
        """
        Sets a value for a given address in the cube.
        Args:
            address:
                A valid cube address.
                Please refer the documentation for further details.
            value:
                The value to be set for the data represented by the address.
        Raises:
            PermissionError:
                If write back is attempted on a read-only Cube.
        """
        if self.settings.read_only:
           raise PermissionError("Write back is not permitted on a read-only cube.")

        context = CubeContext(self)
        context[address].value = value

    def __delitem__(self, address):
        """
        Deletes the records represented by the given address from the underlying
        dataframe of the cube.
        Args:
            address:
                A valid cube address.
                Please refer the documentation for further details.
        Raises:
            PermissionError:
                If write back is attempted on a read-only Cube.
        """
        raise NotImplementedError("Deletion not implemented yet.")

    def slice(self, rows=None, columns=None, measures=None, aggfunc=None,
              sub_totals: bool = True, sort_values: bool = False,
              max_rows: bool | int = False, max_columns: bool | int = True,
              config=None) -> pd.DataFrame:
        """
        Creates and returns a Pandas PivotTable based on the current context. Using the `slice` method
        sophisticated PivotTables can be easily created for printing in Jupyter, visual data analysis and
        reporting purposes by setting and changing rows, columns and filters.

        Please refer to the documentation of the slice methods for further details.

        Args:
            rows:
                (optional) The rows of the slice. Can contain be one or more dimensions with
                or without a member definitions or measures or `None`.

            columns:
                (optional) The columns of the slice. Can contain be one or more dimensions with
                or without a member definitions or measures or `None`.

            measures:
                (optional) The measures/values of the slice. Can be one or more measures, or `None`.

            aggfunc:
                (optional) The aggregation function or functions to be used for the pivot table.
                Default value is 'sum'.

            sub_totals:
                (optional) If sub-totals should be displayed in the pivot table. Default is `True`.

            sort_values:
                (optional) If the values should be sorted in the pivot table. Default is `True`.

            max_rows:
                (optional) The maximum number of rows to be displayed in the pivot table. Either a positive
                integer or a boolean value. If set to `True`, all rows will be shown. If set to `False`,
                the default number of rows (as defined in Pandas) will be shown. Default value is `False`.

            max_columns:
                (optional) The maximum number of columns to be displayed in the pivot table. Either a positive
                integer or a boolean value. If set to `True`, all columns will be shown. If set to `False`,
                the default number of columns (as defined in Pandas) will be shown. Default value is `True`.

            config:
                (optional) A slice configuration as a dictionary, a json string or a path to an existing
                file containing the configuration. Slice configurations can be used to define a more
                complex layout. Please refer to the documentation of the slice method for further details.

        Returns:
            A Pandas DataFrame representing the pivot table.

        Raises:
            ValueError:
                If the values for the paramerters rows, columns, filters or config are invalid.

        Samples:
            >>> cdf = cubed(df)
            >>> cdf.slice(rows="product", columns="region")
            ------------------------------------
            |  Sales  | (all) | North | South |
            ------------------------------------
            | (all)   |   550 |   300 |   250 |
            | Apple   |   200 |   100 |   100 |
            | Banana  |   350 |   200 |   150 |
        """
        return CubeContext(self).slice(rows=rows, columns=columns, measures=measures, aggfunc=aggfunc,
                                       sub_totals=sub_totals, sort_values=sort_values,
                                       max_rows=max_rows, max_columns=max_columns,
                                       config=config)

    # endregion

    # region Dunder Methods
    def __str__(self):
        if self._runs_in_jupyter:
            return f"Jupyter Cube({len(self._df)} records, {len(self._dimensions)} dimensions, {len(self._measures)} measures)"
        else:
            return f"Cube({len(self._df)} records, {len(self._dimensions)} dimensions, {len(self._measures)} measures)"

    def __repr__(self):
        if self._runs_in_jupyter:
            from IPython.display import display
            display(f"Cube({len(self._df)} records, {len(self._dimensions)} dimensions, {len(self._measures)} measures)")
            display(self._df)
            return ""
        else:
            return f"Cube({len(self._df)} records, {len(self._dimensions)} dimensions, {len(self._measures)} measures)"
    # endregion

    # region Helper Methods
    @staticmethod
    def _runs_in_jupyter():
        """Returns True if the code runs in a Jupyter notebook, otherwise False."""
        return 'ipykernel' in sys.modules
    # endregion
