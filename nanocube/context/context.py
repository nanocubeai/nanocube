# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

from typing import SupportsFloat, TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from nanocube.context.enums import ContextFunction, ContextAllocation

# ___noinspection PyProtectedMember
if TYPE_CHECKING:
    from nanocube.cube import Cube
    from nanocube.schema import Measure
    from nanocube.schema import Dimension

    # all subclasses of Context listed here:
    from nanocube.context.measure_context import MeasureContext
    from nanocube.context.dimension_context import DimensionContext
    from nanocube.context.member_context import MemberContext
    from nanocube.context.context_context import ContextContext
    from nanocube.context.function_context import FunctionContext
    from nanocube.context.filter_context import FilterContext
    from nanocube.context.member_not_found_context import MemberNotFoundContext
    from nanocube.context.cube_context import CubeContext
    from nanocube.context.boolean_operation_context import BooleanOperationContext
    from nanocube.context.slice import Slice


class Context(SupportsFloat):
    """
    A context represents a multi-dimensional data context or area from within a cube. Context objects can
    be used to navigate and access the data of a cube and thereby the underlying dataframe.

    Cells behave like Python floats and return a numeric aggregation of the
    underlying data. They are intended to be used in mathematical operations.

    Samples:
        >>> cdf = cubed(df)
        >>> value = cdf.A + cdf.B / 2
        200
        >>> cdf.A *= 2
    """

    # region Initialization
    def __init__(self, cube: 'Cube', address: Any, parent: Context | None = None,
                 row_mask: np.ndarray | None = None, member_mask: np.ndarray | None = None,
                 measure: str | None | Measure = None, dimension: str | None | Dimension = None,
                 function: ContextFunction = ContextFunction.SUM,
                 resolve: bool = True, filtered: bool = False, dynamic_attribute: bool = False):
        """
        Initializes a new Context object. For internal use only.
        Raises:
            ValueError:
                If the address is invalid and does not refer to a
                dimension, member or measure of the cube.
        """

        self._use_new_approach: bool = True  # for DEV purposes only...

        self._semaphore: bool = False
        self._cube: Cube = cube
        self._address = address
        self._parent: Context = parent
        self._df: pd.DataFrame = cube.df
        self._row_mask: np.ndarray | None = row_mask
        self._member_mask: np.ndarray | None = member_mask
        self._measure: Measure | None = measure
        self._dimension: Dimension | None = dimension
        self._function: ContextFunction = function

        self._convert_values_to_python_data_types: bool = True
        self._is_filtered: bool = filtered
        self._dynamic_attribute: bool = dynamic_attribute
        self._resolved: bool = False

        if resolve and cube.settings.eager_evaluation:
            from nanocube.context.context_resolver import ContextResolver
            resolved = ContextResolver.resolve(parent=self, address=address, dynamic_attribute=False)
            self._row_mask = resolved.row_mask
            self._measure = resolved.measure
            self._dimension = resolved.dimension
            self._resolved: bool = True

    def __new__(cls, *args, **kwargs):
        return SupportsFloat.__new__(cls)

    # endregion

    # region Public properties and methods
    @property
    def function(self) -> ContextFunction:
        """
        Returns:
            The aggregation function that will be applied to the current context.
        """
        return self._function

    @property
    def value(self):
        """
        Returns:
             The sum value of the current context from the underlying cube.
        """
        return self._evaluate(self._row_mask, self._measure, self._function)

    @value.setter
    def value(self, value):
        """
        Writes a value to the current context of the cube down to the underlying dataframe.
        """
        allocation_function = ContextAllocation.DISTRIBUTE
        self._allocate(self._row_mask, self.measure, value, allocation_function)

    def set_value(self, value, allocation_function: ContextAllocation = ContextAllocation.DISTRIBUTE):
        """
        Writes a value to the current context of the cube down to the underlying dataframe.
        The allocation method can be chosen.

        Args:
            value:
                The value to be written to the cube.
            allocation_function:
                The allocation function to be used for writing the value to the cube.
        Returns:
            The new value of the current context from the underlying cube.
        """
        self._allocate(self._row_mask, self.measure, value, allocation_function)
        return self.value

    @property
    def numeric_value(self) -> float:
        """
        Returns:
             The numerical value of the current context from the underlying cube.
        """
        value = self.value
        if isinstance(value, (float, np.floating)):
            return float(value)
        if isinstance(value, (int, np.integer, bool)):
            return int(value)
        else:
            return 0.0

    @property
    def cube(self) -> Cube:
        """
        Returns:
             The Cube object the Context belongs to.
        """
        return self._cube

    @property
    def dimension(self) -> Dimension:
        """
        Returns:
             The Cube object the Context belongs to.
        """
        return self._dimension

    @property
    def parent(self) -> Context:
        """
        Returns:
             The parent Context of the current Context. If the current Context is the root Context of the cube,
             then the parent Context will be `None`.
        """
        return self._parent

    @property
    def df(self) -> pd.DataFrame:
        """Returns:
        Returns a new Pandas dataframe with all column of the underlying dataframe
        of the Cube, but only with the rows that are represented by the current context.

        The returned dataframe is always a copy of the original dataframe, even if
        the context is not filtering any rows from the underlying dataframe. The returned
        dataframe can be used for further processing outside the cube.

        """
        if self._row_mask is None:
            return self._cube.df  #
        return self._cube.df.iloc[self._row_mask]

    def cubed(self) -> Cube:
        """
        Returns:
            If the current context is filtered, a new Pandas dataframe with all columns
            of the underlying dataframe of the current Cube, containing only the filtered rows will
            be created, wrapped in Cube and returned. If the current context is not filtered, the
            initial dataframe will be reused.

            Note Calling this method `cdf.Apple.cubed() is identical to calling `cubed(cdf.Apple.df)`.
        """
        from nanocube.common import cubed as cubed_method
        return cubed_method(self.df)

    def sample(self, n=None, frac=None, replace=False, weights=None, random_state=None):
        """
        Return a random sample of items from dimension of the cube.
        You can use random_state for reproducibility. The call will be delegated to the underlying Pandas
        dataframe sample method.

        Arguments:
            n: (optional) Number of items from axis to return. Cannot be used with frac. Default = 1 if frac = None.
            frac: (optional) Fraction of axis items to return. Cannot be used with n.
            replace: (optional) Allow or disallow sampling of the same row more than once.
            weights: (optional) Default ‘None’ results in equal probability weighting. If passed a Series,
                will align with target object on index. Index values in weights not found in sampled object
                will be ignored and index values in sampled object not in weights will be assigned weights
                of zero. If called on a DataFrame, will accept the name of a column when axis = 0. Unless
                weights are a Series, weights must be same length as axis being sampled. If weights do not sum
                to 1, they will be normalized to sum to 1. Missing values in the weights column will be treated
                as zero. Infinite values not allowed.
            random_state: (optional) int, array-like, BitGenerator, np.random.RandomState, np.random.Generator.
                If int, array-like, or BitGenerator, seed for random number generator.
                If np.random.RandomState or np.random.Generator, use as given.
        """
        raise NotImplementedError("The sample method is not yet implemented.")



    @property
    def address(self) -> any:
        """
        Returns:
            The address of the current context, as defined by the user
            This does not represent the full address and context down to the cube.
        """
        return self._address

    @property
    def measure(self) -> Measure:
        """
        Returns:
            The Measure object the Context is currently referring to.
            The measure refers to a column in the underlying dataframe
            that is used to calculate the value of the context.
        """
        return self._measure

    @measure.setter
    def measure(self, value: Measure | str):
        """
        Sets the measure of the context.
        """
        if isinstance(value, str):
            if value in self._cube.schema.measures:
                self._measure = self._cube.schema.measures[value]
            else:
                raise ValueError(f"Failed to set context measure '{value}'. "
                                 f"The measure is con contained in the cube schema.")
        self._measure = value

    @property
    def is_filtered(self) -> bool:
        """
        Returns True if the context is somehow filtered and does not represent the full underlying data context.
        """
        return self._is_filtered

    @property
    def is_valid(self):
        """
        Returns True if the context is valid and can be resolved and evaluated.
        """
        return True

    @property
    def row_mask(self) -> np.ndarray | None:
        """
        Returns:
            The row mask of the context. The row mask is represented by a Numpy ndarray
            of the indexes of the rows represented by the current context. The row mask can be used
            for subsequent processing of the underlying dataframe outside the cube.
        """
        return self._row_mask

    @property
    def member_mask(self) -> np.ndarray | None:
        """
        Returns:
            The member mask of the context. If the context refers to a member or a set of members from a dimension.
            then a Numpy ndarray containing the indexes of the rows representing the members is returned.
            `None` is returned otherwise.
            The row mask can be used for subsequent processing of the underlying dataframe outside the cube.
        """
        return self._member_mask

    @property
    def row_mask_inverse(self) -> np.ndarray:
        """
        Returns:
            The inverted row mask of the context. The inverted row mask is represented by a Numpy ndarray
            of the indexes of the rows NOT represented by the current context. The inverted row mask
            can be used for subsequent processing of the underlying dataframe outside the cube.
        """
        return np.setdiff1d(self._cube._df.index.to_numpy(), self._row_mask)

    # endregion

    # region Member related methods and properties
    def top(self, n: int) -> list:
        """
        Returns the top n members of the current context.
        Args:
            n:
                The number of top members to be returned.
        Returns:
            A list of the top n members of the current context.
        """
        return self._get_top_bottom_member(n, return_bottom=False)

    def bottom(self, n: int) -> list:
        """
        Returns the bottom n members of the current context.
        Args:
            n:
                The number of bottom members to be returned.
        Returns:
            A list of the bottom n members of the current context.
        """
        return self._get_top_bottom_member(n, return_bottom=True)

    def _get_top_bottom_member(self, n: int, return_bottom: bool=False) -> list:
        """Returns the top or bottom n members of the current context."""
        if n < 1:
            raise ValueError(f"Invalid value for argument 'n'. Expected a positive integer, but got '{n}'.")

        if self._dimension is None:
            raise ValueError(f"Current context does not contain any DimensionContext to derive members from.")

        col_dim = self._dimension.column
        col_msr = self._measure.column
        if self._row_mask is None:
            top_members = (self._df[[col_dim,col_msr]]
                           .groupby(col_dim).agg('sum')
                           .sort_values([col_dim,col_msr],ascending = return_bottom)
                           .head(n))
        else:
            top_members = (self._df[self._row_mask][[col_dim,col_msr]]
                           .groupby(col_dim).agg('sum')
                           .sort_values([col_dim,col_msr],ascending = return_bottom)
                           .head(n))
        top_members = top_members[col_msr].index.tolist()
        return top_members



    # region - Dynamic attribute resolving
    def __getattr__(self, name) -> (Context | 'MeasureContext' | 'DimensionContext' | 'MemberContext'
                                    | 'FilterContext' | 'BooleanOperationContext' | 'ContextContext'
                                    | 'FunctionContext' | 'MemberNotFoundContext' | 'CubeContext' | Any):
        """Dynamically resolves member from the cube and predecessor cells."""
        # remark: This pseudo-semaphore is not threadsafe. Needed to prevent infinite __getattr__ loops.

        # Special cases: running in Jupyter Notebook, we need to ignore certain attribute requests
        if self._cube._runs_in_jupyter:
            if name == "_ipython_canary_method_should_not_exist_" or name == "shape":
                raise AttributeError()
            if "_repr_" in name or "_ipython_" in name:
                raise AttributeError()
        else:
            if self._semaphore:
                raise AttributeError(
                    f"CubedPandas: Unexpected fatal error while trying to resolve context for '{name}'.")
        if name == "_ipython_canary_method_should_not_exist": # pragma: no cover
            raise AttributeError("cubedpandas")

        # Very special & ugly case:
        # Numpy is requesting the '__array_priority__' property. This occurs only, when a Numpy
        # NDArray contains heterogeneous data types, what is for instance always the case when a
        # column contains NaN values. When now a comparison between a Numpy scalar value,
        # e.g. of type float64, and a CubedPandas context object is requested, Numpy tries to
        # determine the priority in which the left and right arguments of the comparison should
        # be evaluated. Therefor, it asks for the '__array_priority__' property of the other object,
        # here our CubedPandas context object, which prings us into the __getattr__ method.
        # To prevent subsequent errors, we need to catch this request and return a high priority value.
        # For details further see: https://github.com/numpy/numpy/issues/4766 and
        # https://stackoverflow.com/questions/49751000/how-does-numpy-determine-the-array-data-type-when-it-contains-multiple-dtypes
        if name == "__array_priority__":
            return 1000

        try:
            # check for callable aggregation functions, e.g. sum(), avg(), etc.
            from nanocube.context.function_context import FunctionContext
            callable_function = None
            if name.upper() in FunctionContext.KEYWORDS:
                agg_function = getattr(self, f"_agg_{name.lower()}")
                if callable(agg_function):
                    callable_function = agg_function

            # check for attributes
            from nanocube.context.context_resolver import ContextResolver
            self._semaphore = True
            if str(name).endswith("_"):
                name = str(name)[:-1]
                from nanocube.context.filter_context import FilterContext
                if name != "":
                    context = ContextResolver.resolve(parent=self, address=name, dynamic_attribute=True)
                    resolved = FilterContext(context)
                else:
                    resolved = FilterContext(self)
            else:
                resolved = ContextResolver.resolve(parent=self, address=name, dynamic_attribute=True)
            self._semaphore = False

            if callable_function is not None:
                from nanocube.context.function_context import FunctionContext
                if isinstance(resolved, FunctionContext):
                    resolved._callable_function = callable_function

            return resolved

        except ValueError as e:
            self._semaphore = False
            if self._cube.settings.debug_mode:
                raise e
            else:
                # As key errors will occur quite often, e.g. due to typos, we do not want
                # to not confuse the user with the full error trace stack, but just the error message.
                raise ValueError(f"CubedPandas: {str(e)}") from None
        except Exception as e:
            # All unexpected errors
            self._semaphore = False
            raise e

    # endregion

    # region Context manipulation via indexing/slicing
    def __getitem__(self, address):
        """
        Returns a nested context of the cube and for a given address.
        Subsequent nested cells can bee seen as subsequent filters upon the underlying dataframe.

        Args:
            address:
                A valid cube address.
                Please refer the documentation for further details.

        Returns:
            A Context object that represents the cube data related to the address
            and all predecessor cells down to the cube.

        Raises:
            ValueError:
                If the address is not valid or can not be resolved.
        """
        # special case, Cube is called from within a Jupyter Notebook, that requests the context
        if isinstance(address, str) and address.startswith("_ipython_"):
            raise AttributeError("cubedpandas")

        from nanocube.context.context_resolver import ContextResolver
        return ContextResolver.resolve(parent=self, address=address, dynamic_attribute=self._dynamic_attribute)

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
        raise NotImplementedError("Write back is not yet implemented.")
        # row_mask, measure = self._cube._resolve_address(address, self.mask, self.measure)
        # self._cube._write_back(row_mask, measure, value)

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
        row_mask, measure = self._cube._resolve_address(address, self._row_mask, self.measure)
        self._cube._delete(row_mask, measure)

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
            >>> cdf.year["2000"].slice(rows="product", columns="region")
            ------------------------------------
            year: 2000
            ------------------------------------
            |  Sales  | (all) | North | South |
            ------------------------------------
            | (all)   |   550 |   300 |   250 |
            | Apple   |   200 |   100 |   100 |
            | Banana  |   350 |   200 |   150 |
        """
        from nanocube.context.slice import Slice
        slice = Slice(self, rows=rows, columns=columns, measures=measures, aggfunc=aggfunc,
                      sub_totals=sub_totals, sort_values=sort_values,
                      max_rows=max_rows, max_columns=max_columns,
                      config=config)
        return slice.pivot_table

    def filter(self, filter: Any) -> Context:
        """
        Filters the current context by a given filter expression, criteria or callable function.
        Args:
            filter:
                The filter expression, criteria or callable function to be used for filtering the context.
        Returns:
            A new context with the filtered data.
        """
        from nanocube.context.context_resolver import ContextResolver
        return ContextResolver.resolve(parent=self, address=filter, dynamic_attribute=False)

    # endregion

    # region Evaluation functions
    def _get_row_mask(self, before_dimension: Dimension | None) -> np.ndarray | None:
        if self._dimension != before_dimension:
            return self._row_mask
        if self._parent is not None:
            return self._parent._get_row_mask(before_dimension)
        else:
            return None

    def _resolve(self):
        from nanocube.context.context_resolver import ContextResolver
        if self._parent is not None and not self._parent._resolved:
            self._parent._resolve()  # recursive resolve parents, if required
        resolved = ContextResolver.resolve(parent=self, address=self.address, dynamic_attribute=self._dynamic_attribute)
        self._row_mask = resolved.row_mask
        self._measure = resolved.measure
        self._dimension = resolved.dimension
        self._resolved: bool = True


    def _resolve_measure(self) -> Measure:
        """
        Resolves the measure for the current context.
        Returns:
            The resolved Measure object.
        """
        if self._measure is None:
            if self._parent is None:
                self._measure = self._cube.schema.measures.default
            else:
                self._measure = self._parent._resolve_measure()
        return self._measure

    def _evaluate(self, row_mask, measure, operation: ContextFunction = ContextFunction.SUM):
        # Evaluates the value of the current context.
        # Note: This method uses and operates directly on internal Numpy ndarray used by the
        # underlying Pandas dataframe. Therefore, no expensive data copying is required.

        # Get a reference to the underlying Numpy ndarray for the current measure column.
        if measure is None:
            # Resolve the measure if not provided.
            measure = self._resolve_measure()
            if measure is None:
                # The cube has no measures defined
                # So we simply count the number of records.
                if row_mask is None:
                    return len(self._df.index)
                return len(row_mask)

        if row_mask is not None and row_mask.size == 0:
            # no records found -> the context does not exist
            if operation >= ContextFunction.COUNT:
                return 0
            elif pd.api.types.is_integer_dtype(self._df[measure.column]):
                if self._cube.settings.return_none_for_non_existing_cells:
                    return None
                else:
                    return 0
            else:
                if self._cube.settings.return_none_for_non_existing_cells:
                    return None
                else:
                    return 0.0  # return default value

        # Get and filter the values array by the row mask.
        values = self._df[measure.column].to_numpy()
        if row_mask is not None:
            values: np.ndarray = values[row_mask]

        # Evaluate the final value based on the aggregation operation.
        match operation:
            case ContextFunction.SUM:
                value = np.nansum(values)
            case ContextFunction.AVG:
                value = np.nanmean(values)
            case ContextFunction.MEDIAN:
                value = np.nanmedian(values)
            case ContextFunction.MIN:
                value = np.nanmin(values)
            case ContextFunction.MAX:
                value = np.nanmax(values)
            case ContextFunction.COUNT:
                value = len(values)
            case ContextFunction.STD:
                value = np.nanstd(values)
            case ContextFunction.VAR:
                value = np.nanvar(values)
            case ContextFunction.POF:
                value = float(np.nansum(values)) / float(self.cube.df[str(measure)].sum())
            case ContextFunction.NAN:
                value = np.count_nonzero(np.isnan(values))
            case ContextFunction.AN:
                value = np.count_nonzero(~np.isnan(values))
            case ContextFunction.ZERO:
                value = np.count_nonzero(values == 0)
            case ContextFunction.NZERO:
                value = np.count_nonzero(values)
            case _:
                value = np.nansum(values)  # default operation is SUM

        # Convert the value from Numpy to Python data type if required.
        if self._convert_values_to_python_data_types:
            value = self._convert_to_python_type(value)
        return value

    def _agg_sum(self) -> float | int:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.SUM)

    def _agg_avg(self) -> float:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.AVG)

    def _agg_mean(self) -> float:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.AVG)

    def _agg_median(self) -> float:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.MEDIAN)

    def _agg_min(self) -> float | int:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.MIN)

    def _agg_max(self) -> float | int:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.MAX)

    def _agg_count(self) -> int:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.COUNT)

    def _agg_std(self) -> float:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.STD)

    def _agg_var(self) -> float:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.VAR)

    def _agg_pof(self) -> float:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.POF)

    def _agg_nan(self) -> int:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.NAN)

    def _agg_an(self) -> int:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.AN)

    def _agg_zero(self) -> int:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.ZERO)

    def _agg_nzero(self) -> int:
        return self._evaluate(self._row_mask, self._measure, ContextFunction.NZERO)



    def _allocate(self, row_mask: np.ndarray | None = None, measure: Measure | None = None, value: Any = None,
                  operation: ContextAllocation = ContextAllocation.DISTRIBUTE):
        """Allocates a value to the underlying dataframe to support write back operations."""

        if self.cube.settings.read_only:
            raise PermissionError("Write back is not permitted on a read-only cube. "
                                  "Set attribute `read_only` to `False`. "
                                  "Please not that values in the underlying dataframe will be changed.")

        if measure is None:
            # Resolve the measure if not provided.
            measure = self._resolve_measure()
            if measure is None:
                # The cube has no measures defined
                # So we simply count the number of records.
                if row_mask is None:
                    return len(self._df.index)
                return len(row_mask)

        # Get values to update or delete
        value_series = self._df[measure.column].to_numpy()
        if row_mask is None:
            row_mask = self._df.index.to_numpy()
            values: np.ndarray = value_series
        else:
            values: np.ndarray = value_series[row_mask]

        # update values based on the requested operation
        match operation:
            case ContextAllocation.DISTRIBUTE:
                current = sum(values)
                if current != 0:
                    factor = value / current
                    values = values * factor
            case ContextAllocation.SET:
                values = np.full_like(values, value)
            case ContextAllocation.DELTA:
                values = values + value
            case ContextAllocation.MULTIPLY:
                values = values * value
            case ContextAllocation.ZERO:
                values = np.zeros_like(values)
            case ContextAllocation.NAN:
                # todo: this raises the following Numpy warning, but works as expected. What to do?
                # /opt/hostedtoolcache/Python/3.11.9/x64/lib/python3.11/site-packages/numpy/_core/numeric.py:457:
                # RuntimeWarning: invalid value encountered in cast multiarray.copyto(res, fill_value, casting='unsafe')
                # Is this the fix?
                if np.issubdtype(values.dtype, np.integer):
                    values = np.zeros_like(values)
                else:
                    values = np.full_like(values, np.nan)
            case ContextAllocation.DEL:
                raise NotImplementedError("Not yet implemented.")
            case _:
                raise ValueError(f"Allocation operation {operation} not supported.")

        # update the values in the dataframe
        updated_values = pd.DataFrame({measure.column: values}, index=row_mask)
        self._df.update(updated_values)
        return True

    def _delete(self, row_mask: np.ndarray | None = None, measure: Any = None):
        """Deletes all rows defined by the row_mask from the dataframe."""
        self._df.drop(index=row_mask, inplace=True, errors="ignore")
        # not yet required:  self._df.reset_index(drop=True, inplace=True)
        pass

    @staticmethod
    def _convert_to_python_type(value):
        if isinstance(value, (np.integer, int)):
            return int(value)
        elif isinstance(value, (np.floating, float)):
            return float(value)
        elif isinstance(value, (np.datetime64, pd.Timestamp)):
            return pd.Timestamp(value).to_pydatetime()
        elif isinstance(value, (np.bool_, bool)):
            return bool(value)
        elif isinstance(value, (np.ndarray, pd.Series, list, tuple)):
            if isinstance(value, np.ndarray):
                value = value.tolist()
            return [Context._convert_to_python_type(v) for v in value]
        else:
            return value

    # endregion

    # region Dunder methods, operator overloading, float behaviour etc.
    def __contains__(self, key):
        from nanocube.context.dimension_context import DimensionContext
        if isinstance(self, DimensionContext):
            return key in self.members
        raise ValueError(f"Context object of type '{type(self)}' does not support the 'in' operator.")

    def __float__(self) -> float:  # type conversion to float
        return self.numeric_value

    def __index__(self) -> int:  # type conversion to int
        return int(self.numeric_value)

    def __neg__(self):  # - unary operator
        return - self.numeric_value

    def __pos__(self):  # + unary operator
        return self.numeric_value

    def __add__(self, other):  # + operator
        return self.numeric_value + other

    def __iadd__(self, other):  # += operator
        if isinstance(other, Context):
            other = other.numeric_value
        elif not isinstance(other, (int, float)):
            raise ValueError(f"'+=' operator is not supported for values of type '{type(other)}', but only for numeric values.")
        self.value = self.numeric_value + other
        return self

    def __radd__(self, other):  # + operator
        return other + self.numeric_value

    def __sub__(self, other):  # - operator
        return self.numeric_value - other

    def __isub__(self, other):  # -= operator
        if isinstance(other, Context):
            other = other.numeric_value
        elif not isinstance(other, (int, float)):
            raise ValueError(f"'-=' operator is not supported for values of type '{type(other)}', but only for numeric values.")
        self.value = self.numeric_value - other
        return self

    def __rsub__(self, other):  # - operator
        return other - self.numeric_value

    def __mul__(self, other):  # * operator
        return self.numeric_value * other

    def __imul__(self, other):  # *= operator
        if isinstance(other, Context):
            other = other.numeric_value
        elif not isinstance(other, (int, float)):
            raise ValueError(f"'*=' operator is not supported for values of type '{type(other)}', but only for numeric values.")
        self.value = self.numeric_value * other
        return self

    def __rmul__(self, other):  # * operator
        return self.numeric_value * other

    def __floordiv__(self, other):  # // operator (returns an integer)
        return self.numeric_value // other

    def __ifloordiv__(self, other):  # //= operator (returns an integer)
        if isinstance(other, Context):
            other = other.numeric_value
        elif not isinstance(other, (int, float)):
            raise ValueError(f"'//' operator is not supported for values of type '{type(other)}', but only for numeric values.")
        self.value = self.numeric_value // other
        return self

    def __rfloordiv__(self, other):  # // operator (returns an integer)
        return other // self.numeric_value

    def __truediv__(self, other):  # / operator (returns a float)
        return self.numeric_value / other

    def __itruediv__(self, other):  # /= operator (returns a float)
        if isinstance(other, Context):
            other = other.numeric_value
        elif not isinstance(other, (int, float)):
            raise ValueError(f"'/=' operator is not supported for values of type '{type(other)}', but only for numeric values.")
        self.value = self.numeric_value / other
        return self

    def __idiv__(self, other):  # /= operator (returns a float)
        if isinstance(other, Context):
            other = other.numeric_value
        elif not isinstance(other, (int, float)):
            raise ValueError(f"'/=' operator is not supported for values of type '{type(other)}', but only for numeric values.")
        self.value = self.numeric_value / other
        return self

    def __rtruediv__(self, other):  # / operator (returns a float)
        return other / self.numeric_value

    def __mod__(self, other):  # % operator (returns a tuple)
        return self.numeric_value % other

    def __imod__(self, other):  # %= operator (returns a tuple)
        if isinstance(other, Context):
            other = other.numeric_value
        elif not isinstance(other, (int, float)):
            raise ValueError(f"'%=' operator is not supported for values of type '{type(other)}', but only for numeric values.")
        new_value = self.numeric_value % other
        self.value = new_value
        return self

    def __rmod__(self, other):  # % operator (returns a tuple)
        return other % self.numeric_value

    def __divmod__(self, other):  # div operator (returns a tuple)
        return divmod(self.numeric_value, other)

    def __rdivmod__(self, other):  # div operator (returns a tuple)
        return divmod(other, self.numeric_value)

    def __pow__(self, other, modulo=None):  # ** operator
        return self.numeric_value ** other

    def __ipow__(self, other, modulo=None):  # **= operator
        if isinstance(other, Context):
            other = other.numeric_value
        elif not isinstance(other, (int, float)):
            raise ValueError(f"'**=' operator is not supported for values of type '{type(other)}', but only for numeric values.")
        self.value = self.numeric_value ** other
        return self

    def __rpow__(self, other, modulo=None):  # ** operator
        return other ** self.numeric_value

    def __lt__(self, other):  # < (less than) operator
        from nanocube.context.measure_context import MeasureContext
        if isinstance(self, MeasureContext) and self.is_filtered:
            from nanocube.context.filter_context import FilterContext
            context = FilterContext(self)
            return context < other
        return self.numeric_value < other

    def __gt__(self, other):  # > (greater than) operator
        from nanocube.context.measure_context import MeasureContext
        if isinstance(self, MeasureContext) and self.is_filtered:
            from nanocube.context.filter_context import FilterContext
            context = FilterContext(self)
            return context > other
        return self.numeric_value > other

    def __le__(self, other):  # <= (less than or equal to) operator
        from nanocube.context.measure_context import MeasureContext
        if isinstance(self, MeasureContext) and self.is_filtered:
            from nanocube.context.filter_context import FilterContext
            context = FilterContext(self)
            return context <= other
        return self.numeric_value <= other

    def __ge__(self, other):  # >= (greater than or equal to) operator
        from nanocube.context.measure_context import MeasureContext
        if isinstance(self, MeasureContext) and self.is_filtered:
            from nanocube.context.filter_context import FilterContext
            context = FilterContext(self)
            return context >= other
        return self.numeric_value >= other

    def __eq__(self, other):  # == (equal to) operator
        from nanocube.context.measure_context import MeasureContext
        if isinstance(self, MeasureContext) and self.is_filtered:
            from nanocube.context.filter_context import FilterContext
            context = FilterContext(self)
            return context == other
        return self.numeric_value == other

    def __ne__(self, other):  # != (not equal to) operator
        from nanocube.context.measure_context import MeasureContext
        if isinstance(self, MeasureContext) and self.is_filtered:
            from nanocube.context.filter_context import FilterContext
            context = FilterContext(self)
            return context != other
        return self.numeric_value != other

    def __and__(self, other):  # AND operator (A & B)
        if isinstance(other, Context):
            from nanocube.context.boolean_operation_context import BooleanOperationContext, \
                BooleanOperation
            return BooleanOperationContext(self, other, BooleanOperation.AND)
        return self.numeric_value and other

    def __iand__(self, other):  # inplace AND operator (a &= b)
        if isinstance(other, Context):
            from nanocube.context.boolean_operation_context import BooleanOperationContext, \
                BooleanOperation
            return BooleanOperationContext(self, other, BooleanOperation.AND)
        return self.numeric_value and other

    def __rand__(self, other):  # and operator
        if isinstance(other, Context):
            from nanocube.context.boolean_operation_context import BooleanOperationContext, \
                BooleanOperation
            return BooleanOperationContext(self, other, BooleanOperation.AND)
        return self.numeric_value and other

    def __or__(self, other):  # OR operator (A | B)
        if isinstance(other, Context):
            from nanocube.context.boolean_operation_context import BooleanOperationContext, \
                BooleanOperation
            return BooleanOperationContext(self, other, BooleanOperation.OR)
        return self.numeric_value or other

    def __ior__(self, other):  # inplace OR operator (A |= B)
        if isinstance(other, Context):
            from nanocube.context.boolean_operation_context import BooleanOperationContext, \
                BooleanOperation
            return BooleanOperationContext(self, other, BooleanOperation.OR)
        return self.numeric_value or other

    def __ror__(self, other):  # or operator
        if isinstance(other, Context):
            from nanocube.context.boolean_operation_context import BooleanOperationContext, \
                BooleanOperation
            return BooleanOperationContext(self, other, BooleanOperation.OR)
        return other or self.numeric_value

    def __xor__(self, other):  # xor operator
        if isinstance(other, Context):
            from nanocube.context.boolean_operation_context import BooleanOperationContext, \
                BooleanOperation
            return BooleanOperationContext(self, other, BooleanOperation.XOR)
        return self._value ^ other

    def __invert__(self):  # ~ operator
        # Special case: NOT operation > inverts the row mask
        from nanocube.context.boolean_operation_context import BooleanOperationContext, BooleanOperation
        return BooleanOperationContext(self, operation=BooleanOperation.NOT)

    def __abs__(self):
        return self.numeric_value.__abs__()

    def __bool__(self):
        return self.numeric_value.__bool__()

    def __str__(self):
        return self.value.__str__()

    def __repr__(self):
        return self.value.__str__()

    def __round__(self, n=None):
        return self.numeric_value.__round__(n)

    def __trunc__(self):
        return self.numeric_value.__trunc__()

    def __floor__(self):
        return self.numeric_value.__floor__()

    def __int__(self):
        return self.numeric_value.__int__()

    def __ceil__(self):
        return self.numeric_value.__ceil__()

    def __format__(self, format_spec):
        return self.value.__format__(format_spec)

    def __hash__(self):
        context_hash = f"{self._dimension}_{self._address}_{self._measure}".__hash__()
        return context_hash

    # end region


