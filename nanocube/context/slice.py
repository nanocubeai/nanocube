# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from nanocube.context.context import Context

if TYPE_CHECKING:
    from nanocube.cube import Cube
    from nanocube.schema import MeasureCollection
    from nanocube.schema import Measure
    from nanocube.schema import Dimension
    from nanocube.schema import DimensionCollection
    from nanocube.context.dimension_context import DimensionContext
    from nanocube.context.measure_context import MeasureContext
    from nanocube.context.member_context import MemberContext
    from nanocube.context.filter_context import FilterContext
    from nanocube.context.boolean_operation_context import BooleanOperationContext


class Slice:
    """A slice represents a view on a cube, and allows for easy access to the underlying Pandas dataframe.
    Typically, a slice has rows, columns and filter, just like in an Excel PivotTable. Slices
    are easy to define and use for convenient data analysis."""

    def __init__(self, context: Context | 'Cube',
                 rows: Any = None, columns: Any = None,
                 measures: Any = None,
                 aggfunc: None | str | list[str] = None,
                 sub_totals: bool = True,
                 sort_values: bool = False,
                 max_rows: bool | int = False,
                 max_columns: bool | int = True,
                 config: dict | str | None = None):
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

        Examples:
            >>> df = pd.value([{"product": ["A", "B", "C"]}, {"value": [1, 2, 3]}])
            >>> cdf = cubed(df)
            >>> Slice(cdf,"product").print()
            +---+-------+
            |   | value |
            +---+-------+
            | A |     1 |
            | B |     2 |
            | C |     3 |
            +---+-------+
        """
        # input parameters
        from nanocube.cube import Cube
        if isinstance(context, Cube):
            self._cube: Cube = context
            self._context: Context | None = None
        else:
            self._cube: Cube = context.cube
            self._context: Context = context

        self._rows = rows
        self._columns = columns
        self._measures = measures
        self._aggfunc = aggfunc
        self._sub_totals: bool = sub_totals
        self._sort_values: bool = sort_values
        self._max_rows: bool = max_rows
        self._max_columns: bool = max_columns
        self._config = config
        self._pivot_table: pd.DataFrame | None = None

        # Create the slice
        self.create()

    # region Public properties
    @property
    def cube(self) -> 'Cube':
        """Returns the cube the slice refers to."""
        return self._cube

    @property
    def rows(self):
        """Returns the rows of the slice."""
        return self._rows

    @property
    def columns(self):
        """Returns the columns of the slice."""
        return self._columns

    @property
    def measures(self):
        """Returns the measures of the slice."""
        return self._measures

    @property
    def aggfunc(self):
        """Returns the aggregation functions of the slice."""
        return self._aggfunc

    @property
    def sub_totals(self) -> bool:
        """Returns if sub-totals should be shown in the slice."""
        return self._sub_totals

    @property
    def sort_values(self) -> bool:
        """Returns if the values should be sorted in the slice."""
        return self._sort_values

    @property
    def max_rows(self) -> bool | int:
        """Returns if all rows should be shown in the slice."""
        return self._max_rows

    @property
    def max_columns(self) -> bool | int:
        """Returns if all columns should be shown in the slice."""
        return self._max_columns

    @property
    def config(self) -> dict | str | None:
        """Returns the configuration of the slice."""
        return self._config

    @property
    def pivot_table(self) -> pd.DataFrame | None:
        """Returns the Pandas pivot-table represented by the slice."""
        return self._pivot_table

    # endregion

    # region Magic methods
    def __str__(self):
        return f"{self._pivot_table.__str__()}"

    def __repr__(self):
        if self._cube._runs_in_jupyter:
            from IPython.display import display
            display(self._pivot_table)
            return ""
        else:
            return f"{self._pivot_table.__repr__()}"

    # endregion

    # region Public methods
    def show(self):
        """Prints the slice to the console."""
        print(self._pivot_table)

    def to_html(self, classes: str | list | tuple | None = None, style:str= None) -> str | None:
        """Returns the slice as an HTML table."""
        if self._pivot_table is None:
            return None
        html = self._pivot_table.to_html(classes=classes, float_format=self._float_formatter, justify="justify-all")
        if style is not None:
            html = html.replace("<table", f"<table style='{style}'")
        return html

    @staticmethod
    def _float_formatter(x: float) -> str:
        """Formats a float value."""
        return f"{x:,.2f}"

    def create(self, sub_totals: bool = True):
        """Creates the slice based on the current configuration from the underlying cube and dataframe."""

        # 1. evaluate row and columns axis arguments
        row_measures, row_dimensions, row_filters = self._get_axis(self._rows)
        column_measures, column_dimensions, column_filters = self._get_axis(self._columns)
        axis_measures = list(set(row_measures + column_measures))
        axis_filters = list(set(row_filters + column_filters))

        # 1. get the relevant rows from the current context
        row_mask = self._context.row_mask
        for filter in axis_filters:
            if row_mask is None:
                row_mask = filter.row_mask
            else:
                row_mask = np.intersect1d(row_mask, filter.row_mask)
        if row_mask is None:
            df = self._cube._df
        else:
            df = self._cube._df.iloc[row_mask]

        # 3. If no rows or columns are defined, we simply aggregate and return all measures as a normal dataframe
        if len(row_dimensions) == 0 and len(column_dimensions) == 0:
            agg_functions = ["sum", "min", "max", "mean", "median", "std", "var", "count"]
            self._pivot_table = df.agg({measure.column: agg_functions for measure in self._cube.schema.measures})
            return

        # 4. get requested measures
        measures = self._get_axis(self._measures)[0]
        if len(measures) == 0:
            # if no measures defined, check if there are members in the axis...
            if len(axis_measures) > 0:
                measures = axis_measures
            else:
                if len(column_dimensions) > 0:
                    # ...or use the default measure of the cube
                    measures = [self._cube.schema.measures.default, ]
                else:
                    # ...or, if no columns are defined, use all measures of the cube
                    measures = list(self._cube.schema.measures)

        # 5. Set up a Pandas pivot table
        #   1st, the values to be displayed = the measures of the cube
        values = [m.column for m in measures]
        #   2nd, define the aggregation functions to be applied to the values, default is "sum"
        if self._aggfunc is not None:
            if isinstance(self._aggfunc, str):
                agg_functions = [self._aggfunc, ]
            elif isinstance(self._aggfunc, list | tuple | set):
                agg_functions = list(self._aggfunc)
            else:
                raise ValueError(f"Invalid value for argument aggfunc: {self._aggfunc}")
        else:
            agg_functions = ["sum", ]
        agg_functions = [f.lower() for f in agg_functions if
                         f.lower() in ["sum", "min", "max", "mean", "median", "std", "var", "count"]]

        aggfunc = {m.column: agg_functions for m in measures}
        #   3rd, define the rows and columns of the pivot table
        index = [item.column for item in row_dimensions]  # rows
        columns = [item.column for item in column_dimensions]  # columns
        #   4th, create the pivot table
        pvt = pd.pivot_table(df, values=values, index=index, columns=columns, aggfunc=aggfunc,
                             fill_value=0, dropna=True)  # , margins=True, margins_name='(all)')

        # 6. (optional) subsequent processing of the pivot table
        # 6.1 add subtotal of the rows
        if self._sub_totals:
            pvt = self._add_subtotals(pvt, row_dimensions, aggfunc=agg_functions[0])
        # 6.2 sort values in the pivot table rows
        if self._sort_values is not None and self._sort_values != False:
            pvt = self._sort_row_values(pvt=pvt, row_columns=index, sort_measure=self._sort_values,
                                        measures=values, default_measure=values[0])


        # 7. apply pivot table formatting: https://pandas.pydata.org/docs/user_guide/style.html
        pvt.style \
            .format(precision=2, thousands=".", decimal=",") \
            .format_index(str.upper, axis=1) \
            .set_caption("This is a caption") \
            .background_gradient(axis=None, vmin=1, vmax=1000, cmap="YlGnBu")

        # 8. adjust the pivot table to show all rows and columns
        # reset the Pandas display options
        # pd.reset_option('display.max_rows', 0)
        # pd.reset_option('display.max_columns', 0)
        if self._max_rows:
            if isinstance(self._max_rows, bool):
                pd.set_option('display.max_rows', None)
            elif isinstance(self._max_rows, int) and self._max_rows > 0:
                pd.set_option('display.max_rows', self._max_rows)

        if self._max_columns:
            if isinstance(self._max_columns, bool):
                pd.set_option('display.max_columns', None)
            elif isinstance(self._max_columns, int) and self._max_columns > 0:
                pd.set_option('display.max_columns', self._max_columns)

        # we're done
        self._pivot_table = pvt
        return

    # endregion

    # region Internal methods
    def _get_axis(self, axis_definition) -> (list[Measure], list[Dimension]):
        """Extracts the measures and dimensions from a slice axis definition, rows or columns."""

        from nanocube.schema import MeasureCollection
        from nanocube.schema import Measure
        from nanocube.schema import Dimension
        from nanocube.schema import DimensionCollection
        from nanocube.context.dimension_context import DimensionContext
        from nanocube.context.measure_context import MeasureContext
        from nanocube.context.member_context import MemberContext
        from nanocube.context.filter_context import FilterContext
        from nanocube.context.boolean_operation_context import BooleanOperationContext

        list_delimiters = [",", ";", "|"]

        dimensions: list[Dimension] = []  # the list of dimensions to be nested in the axis of the slice
        measures: list[Measure] = []  # the measures to contained in the axis
        filters: list = []

        args = axis_definition if isinstance(axis_definition, list | tuple | set) else [axis_definition, ]
        for arg in args:
            # string arguments
            if isinstance(arg, str):
                if arg == "*":
                    # use all dimensions
                    dimensions.extend([dim for dim in self._cube.schema.dimensions])
                else:
                    if arg in self._cube.schema.dimensions:
                        dimensions.append(self._cube.schema.dimensions[arg])
                    else:
                        # ...maybe we have a list of dimensions like "dim1, dim2, dim3"
                        for delimiter in list_delimiters:
                            if delimiter in arg:
                                items = [item.strip() for item in arg.split(delimiter)]
                                dimensions.extend([dim for dim in self._cube.schema.dimensions if dim.name in items])
                                break

            # cube related object arguments
            elif isinstance(arg, Dimension):
                dimensions.append(arg)
            elif isinstance(arg, DimensionCollection):
                dimensions.extend([dim for dim in arg])
            elif isinstance(arg, DimensionContext):
                dimensions.append(arg.dimension)
            elif isinstance(arg, Measure):
                measures.append(arg)
            elif isinstance(arg, MeasureCollection):
                measures.extend([m for m in arg])
            elif isinstance(arg, MeasureContext):
                measures.append(arg.measure)
                if isinstance(arg.parent, FilterContext):
                    filters.append(arg)
                    if isinstance(arg.parent.parent, DimensionContext | MemberContext):
                        dimensions.append(arg.parent.parent.dimension)
            elif isinstance(arg, DimensionContext):
                dimensions.append(arg.dimension)
            elif isinstance(arg, MemberContext):
                dimensions.append(arg.dimension)
                filters.append(arg)
            elif isinstance(arg, FilterContext):
                dimensions.append(arg.dimension)
                filters.append(arg)
            elif isinstance(arg, BooleanOperationContext):
                filters.append(arg)
            else:
                pass

        return measures, dimensions, filters

    @staticmethod
    def _add_subtotals(pvt: pd.DataFrame, row_dimensions, aggfunc=None, all_member_name: str = "(all)") -> pd.DataFrame:
        """Adds subtotals to a pivot table."""

        dim_count = len(row_dimensions)
        sub_totals = []
        for pos in range(dim_count - 1):
            # aggregate the pivot table rows over all dimensions, except the last/innermost dimension
            levels = [p for p in range(pos + 1)]
            if aggfunc == "sum":
                group = pvt.groupby(level=levels).sum()
            elif aggfunc == "mean":
                group = pvt.groupby(level=levels).mean()
            elif aggfunc == "median":
                group = pvt.groupby(level=levels).median()
            elif aggfunc == "min":
                group = pvt.groupby(level=levels).min()
            elif aggfunc == "max":
                group = pvt.groupby(level=levels).max()
            elif aggfunc == "std":
                group = pvt.groupby(level=levels).std()
            elif aggfunc == "var":
                group = pvt.groupby(level=levels).var()
            elif aggfunc == "count":
                group = pvt.groupby(level=levels).count()
            else:  # default is sum
                group = pvt.groupby(level=levels).sum()

            # adjust the tuples of the group index
            tuples = []
            for item in group.index:
                if isinstance(item, tuple):
                    if len(item) < dim_count:
                        group_tuple = item + (all_member_name,) + tuple(["" for i in range(dim_count - len(item) - 2)])
                    else:
                        group_tuple = item
                        group_tuple[dim_count - 1] = all_member_name
                else:
                    group_tuple = (item,) + (all_member_name,) + tuple(["" for i in range(dim_count - 2)])
                tuples.append(group_tuple)

            group.index = pd.MultiIndex.from_tuples(tuples)
            sub_totals.append(group)

        # add grant total
        group_tuple = (all_member_name,) + tuple(["" for i in range(dim_count - 1)])
        grand_total = pvt.agg(func=aggfunc, axis=0)
        pvt.loc[group_tuple] = grand_total

        # join the subtotals and the pivot table
        segments = [pvt, ]
        segments.extend(sub_totals)

        new_pvt = pd.concat(segments, join="inner")
        new_pvt = new_pvt.sort_index()
        return new_pvt

    @staticmethod
    def _sort_row_values(pvt: pd.DataFrame, row_columns, sort_measure, measures, default_measure,
                         aggfunc="sum") -> pd.DataFrame:
        """Sorts the values in a pivot table."""
        ascending = False
        if isinstance(sort_measure, str):
            measure = sort_measure.upper().strip()
            if "ASC" in measure or "ASCENDING" in measure:
                ascending = True
            if "DESC" in measure or "DESCENDING" in measure:
                ascending = False

            tokens = re.split(': |; |, |\*|\n', sort_measure)
            if len(tokens) > 1:
                sort_measure = tokens[:-1]
            if sort_measure not in measures:
                raise ValueError(f"Invalid measure '{sort_measure}' for sorting in method `slice(...)`.")

            value = sort_measure
        else:
            value = default_measure
        sort_by = [(row_dim, aggfunc) for row_dim in row_columns]
        sort_by = [row_dim for row_dim in row_columns[:-1]]
        sort_order = [ascending for _ in row_columns[:-1]]
        pvt = pvt.sort_values(by=sort_by, ascending=sort_order)
        return pvt

    # endregion
