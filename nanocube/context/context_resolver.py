# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from __future__ import annotations

import datetime
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from nanocube.datespan import DateSpanSet, DateSpan

from nanocube.context.enums import ContextFunction
from nanocube.context.context import Context
from nanocube.context.datetime_resolver import resolve_datetime
from nanocube.context.expression import Expression
from nanocube.context.filter_context import FilterContext
from nanocube.context.function_context import FunctionContext

if TYPE_CHECKING:
    from nanocube.schema import Dimension
    from nanocube.schema import Member, MemberSet
    from nanocube.schema import Measure


class ContextResolver:
    """A helper class to resolve the address of a context."""

    @staticmethod
    def resolve(parent: Context, address, dynamic_attribute: bool = False,
                target_dimension: Dimension | None = None) -> Context:

        # 1. If no address needs to be resolved, we can simply return the current/parent context.
        if address is None:
            return parent

        # unpack the parent context
        cube = parent.cube
        row_mask = parent.row_mask
        member_mask = parent.member_mask
        measure = parent.measure
        dimension = parent.dimension
        address_as_list = None

        # 2. If the address is already a context, then we can simply wrap it into a ContextContext and return it.
        if isinstance(address, Context):
            if parent.cube == address.cube:
                from nanocube.context.context_context import ContextContext
                return ContextContext(parent, address)
            raise ValueError(f"The context handed in as an address argument refers to a different cube/dataframe. "
                             f"Only contexts from the same cube can be used as address arguments.")

        # A user handed a dimension or measure instance from a schema object in,
        # we need to convert it to a string and continue.
        if address.__class__.__name__ == 'Measure' or address.__class__.__name__ == 'Dimension':
            address = str(address)

        # 3. String addresses are resolved by checking for measures, dimensions and members.
        if isinstance(address, str):
            address_with_whitespaces = None
            if dynamic_attribute:
                if cube.settings.auto_whitespace and ("_" in address) and (not address.startswith("_")):
                    address_with_whitespaces = address.replace("_", " ")


            # 3.1. Check for function keywords like SUM, AVG, MIN, MAX, etc.
            if address.upper() in FunctionContext.KEYWORDS:
                function_context = FunctionContext(parent=parent, function=ContextFunction[address.upper()])

                # Special case NAN:
                # NAN is a reserved function keyword as well as the alias for missing values,
                # so we need to check for it if we need to filter for missing values.
                if function_context.dimension is not None:
                    if function_context.function == ContextFunction.NAN:
                        result, row_mask, member_mask = (function_context.dimension.
                                                         _check_exists_and_resolve_member("nan",
                                                                                          function_context.row_mask))
                        if result:
                            function_context._row_mask = row_mask

                return function_context

            # 3.2. Check for names of measures
            if address_with_whitespaces is not None:
                address = address_with_whitespaces if address_with_whitespaces in cube.schema.measures else address
            if address in cube.schema.measures:
                from nanocube.context.measure_context import MeasureContext

                # set the measure for the context to the new resolved measure
                measure = cube.schema.measures[address]
                resolved_context = MeasureContext(cube=cube, parent=parent, address=address, row_mask=row_mask,
                                                  measure=measure, dimension=dimension, resolve=False)
                return resolved_context

            # 3.3. Check for names of dimensions
            if address_with_whitespaces is not None:
                address = address_with_whitespaces if address_with_whitespaces in cube.schema.dimensions else address
            if address in cube.schema.dimensions:
                from nanocube.context.dimension_context import DimensionContext

                dimension = cube.schema.dimensions[address]
                resolved_context = DimensionContext(cube=cube, parent=parent, address=address,
                                                    row_mask=row_mask,
                                                    measure=measure, dimension=dimension, resolve=False)
                if pd.api.types.is_bool_dtype(dimension.dtype):
                    # special case: for boolean dimensions, we assume that the user wants to filter for True values if
                    # the dimension is referenced without a member name: `cube.online` instead of `cube.online[True]`
                    # In this case, we will return a MemberContext with the member mask set to the boolean mask.
                    from nanocube.context.member_context import MemberContext
                    exists, new_row_mask, member_mask = dimension._check_exists_and_resolve_member(True, row_mask)
                    resolved_context = MemberContext(cube=cube, parent=resolved_context, address=True,
                                                   row_mask=new_row_mask, member_mask=member_mask,
                                                   measure=measure, dimension=dimension, resolve=False)
                return resolved_context

            # 3.4. Check if the address contains a list of members, e.g. "A, B, C"
            if address_with_whitespaces is not None:
                address = address_with_whitespaces

            address, address_as_list = ContextResolver.string_address_to_list(cube, address)
            if isinstance(address_as_list, list):
                # The address either represents a member key containing
                # a comma or it should represent a list of members.
                # Let's do quick check if the address is a member key.
                pass

        # 4. Check for callable objects, e.g. lambda functions
        if callable(address):
            success, row_mask = ContextResolver._resolve_callable(parent=parent, row_mask=row_mask,
                                                           measure=measure, dimension=dimension,
                                                           function=address)
            if success:
                return FilterContext(parent=parent, filter_expression=address, row_mask=row_mask,
                                     measure=measure, dimension=dimension, resolve=False, is_comparison=False)

        # 5. check for dict addresss like {"product": "A", "channel": "Online"}
        if isinstance(address, dict):
            is_valid_context, new_context_ref = ContextResolver.resolve_complex(parent, address, dimension)
            if is_valid_context:
                return new_context_ref
            else:
                if parent.cube.settings.ignore_member_key_errors:  # and not dynamic_attribute:
                    if dimension is not None:
                        if cube.df[dimension.column].dtype == pd.DataFrame([address, ])[0].dtype:
                            from nanocube.context.member_not_found_context import MemberNotFoundContext
                            return MemberNotFoundContext(cube=cube, parent=parent, address=address, dimension=dimension)

                raise ValueError(new_context_ref.message)

        # 6. Check for members of all data types over all dimensions in the cube
        #    Let's try start with a dimension that was handed in,
        #    if a dimension was handed in from the parent context.
        if not isinstance(address, list | tuple):

            skip_checks = False
            dimension_list = None
            dimension_switched = False

            # Check for dimension hints and leverage them, e.g. "products:apple", "children:1"
            if target_dimension is not None:
                dimension_list = [target_dimension]
            elif isinstance(address, str) and (":" in address) and address_as_list is None:
                dim_name, member_name = address.split(":")
                if dim_name.strip() in cube.schema.dimensions:
                    new_dimension = cube.schema.dimensions[dim_name.strip()]
                    if dimension is not None:
                        dimension_switched = new_dimension != dimension
                    dimension = new_dimension

                    address = member_name.strip()
                    address = ContextResolver.adjust_data_type(address, dimension)

                    dimension_list = [dimension]
                    skip_checks = True  # let's skip the checks as we have a dimension hint
            if dimension_list is None:
                dimension_list = cube.schema.dimensions.starting_with_this_dimension(dimension)

            for dim in dimension_list:
                if dim == dimension and not dimension_switched:
                    # We are still at the dimension that was handed in, therefore we need to check for
                    # subsequent members from one dimension, e.g., if A, B, C are all members from the
                    # same dimension, then `cube.A.B.C` will require to join the member rows of A, B and C
                    # before we filter the rows from a previous context addressing another or no dimension.
                    address = ContextResolver.adjust_data_type(address, dim)
                    if ContextResolver.matching_data_type(address, dim):
                        parent_row_mask = parent._get_row_mask(before_dimension=dimension)
                        exists, new_row_mask, member_mask = (
                            dimension._check_exists_and_resolve_member(address, parent_row_mask, member_mask,
                                                                       skip_checks=skip_checks))
                    else:
                        exists, new_row_mask, member_mask = False, None, None
                else:
                    # This indicates a dimension context switch,
                    # e.g. from `None` to dimension `A`, or from dimension `A` to dimension `B`.
                    exists, new_row_mask, member_mask = dim._check_exists_and_resolve_member(address, row_mask)

                if exists:
                    # We found the member...
                    from nanocube.schema import Member, MemberSet
                    member = Member(dim, address)
                    members = MemberSet(dimension=dim, address=address, row_mask=new_row_mask,
                                        members=[member])
                    from nanocube.context.member_context import MemberContext
                    resolved_context = MemberContext(cube=cube, parent=parent, address=address,
                                                     row_mask=new_row_mask, member_mask=member_mask,
                                                     measure=measure, dimension=dim,
                                                     members=members, resolve=False)
                    return resolved_context

                # special case for datetime dimensions!
                if dimension is not None and pd.api.types.is_datetime64_any_dtype(dimension.dtype):
                    # As arbitrary date expressions can be used, we use the datespan package to resolve them.
                    dss: DateSpanSet | None = None

                    try:
                        if isinstance(address, slice):  # e.g. "2021-01-01":"2021-12-31"
                            # the 'step' attribute of a slice object will be ignored
                            start, stop = address.start, address.stop
                            if start is None and stop is None:
                                raise ValueError(f"Invalid date range slice '{address}'. "
                                                 f"Both start and stop of slice are None.")
                            if start:  # from start to datetime.max
                                start_date = DateSpanSet(start).start
                                stop_date = DateSpan.MAX_DATE
                            elif stop:  # from datetime.min to stop
                                start_date = DateSpan.MIN_DATE
                                stop_date = DateSpanSet(stop).end
                            else:  # from start to stop
                                start_date = DateSpanSet(start).start
                                stop_date = DateSpanSet(stop).end

                            dss = DateSpanSet(DateSpan(start_date, stop_date))
                        else:
                            dss = DateSpanSet(address)
                    except Exception as e:
                        raise ValueError(f"Invalid date token '{address}' in address '{address}'. {e}")

                    # Filter using the datespan package
                    parent_row_mask = parent._get_row_mask(before_dimension=dimension)
                    filter_func = dss.to_df_lambda()
                    # filter_func_Source = dss.to_df_lambda(return_source_code=True) # for debugging only
                    # if "year=9999" in filter_func_Source:
                    #     pass
                    if parent_row_mask is not None:
                        series = cube.df[dimension.column][parent_row_mask]
                        bool_mask = filter_func(series)
                    else:
                        series = cube.df[dimension.column]
                        bool_mask = filter_func(series)
                    new_row_mask = cube.df[bool_mask].index.to_numpy()
                    if len(new_row_mask) > 0:
                        # some records were found
                        from nanocube.schema import Member, MemberSet
                        member = Member(dim, address)
                        members = MemberSet(dimension=dim, address=address, row_mask=new_row_mask,
                                            members=[member])
                        from nanocube.context.member_context import MemberContext
                        resolved_context = MemberContext(cube=cube, parent=parent, address=address,
                                                         row_mask=new_row_mask, member_mask=member_mask,
                                                         measure=measure, dimension=dim,
                                                         members=members, resolve=False)
                    else:
                        # no records were found, we will return a context with an empty row mask
                        from nanocube.context.member_not_found_context import MemberNotFoundContext
                        resolved_context = MemberNotFoundContext(cube=cube, parent=parent, address=address,
                                                                 dimension=dim)
                    return resolved_context


        if not dynamic_attribute:
            # As we are NOT in a dynamic context like `cube.A.online.sales`, where only exact measure,
            # dimension and member names are supported, and have not yet found a suitable member, we need
            # to check for complex member set definitions like filter expressions, list, dictionaries etc.
            is_valid_context, new_context_ref = ContextResolver.resolve_complex(parent, address, dimension,
                                                                                address_as_list)
            if is_valid_context:
                return new_context_ref
            else:
                if parent.cube.settings.ignore_member_key_errors:  # and not dynamic_attribute:
                    if dimension is not None:
                        if cube.df[dimension.column].dtype == pd.DataFrame([address, ])[0].dtype:
                            from nanocube.context.member_not_found_context import MemberNotFoundContext
                            return MemberNotFoundContext(cube=cube, parent=parent, address=address, dimension=dimension)

                raise ValueError(new_context_ref.message)

        # 7. If we've not yet resolved anything meaningful, then we need to raise an error...
        raise ValueError(f"Invalid member name or address '{address}'. "
                         f"Tip: check for typos and upper/lower case issues.")

    @staticmethod
    def resolve_complex(context: Context, address, dimension: Dimension | None = None,
                        address_as_list: list | None = None) -> tuple[bool, Context]:
        """ Resolves complex member definitions like filter expressions, lists, dictionaries etc. """
        from nanocube.context.cube_context import CubeContext

        if dimension is None:
            dimension = context.dimension

        # Check if we need to process a list of address arguments.
        # This is required as addresses containing a list separator ','
        # can be interpreted as a list of members or as a member name simply containing a ','.
        # Example (true):
        #   "A, B, C" is not an existing member name, so we will check
        #   if the user ment a list of members: ["A", "B", "C"]
        # Example (false):
        #   "Hey, come over." is not an existing member name and also not a valid list of members,
        #   so we will need to raise an ValueError later on.
        if address_as_list is not None:
            address = address_as_list

        if isinstance(address, str):
            # 1. try wildcard expressions like "On*" > resolving e.g. to "Online"
            if "*" in address:
                if dimension is None:
                    if address == "*":
                        # This can only happen if we are still at the cube level, no dimension has been selected yet.
                        # In this case, we will return the cube context to return all records
                        return True, context
                    # We are at the cube level, so we need to consider all dimensions
                    dimensions = context.cube.schema.dimensions
                else:
                    # We are at a dimension level, so we will only consider the current dimension
                    dimensions = [dimension]

                for dim in dimensions:
                    match_found, members = dim.wildcard_filter(address)

                    if match_found:
                        member_mask = None
                        parent_row_mask = context._get_row_mask(before_dimension=context.dimension)
                        exists, new_row_mask, member_mask = (
                            dim._check_exists_and_resolve_member(member=members, row_mask=parent_row_mask,
                                                                 parent_member_mask=member_mask,
                                                                 skip_checks=True))
                        if exists:
                            from nanocube.schema import MemberSet
                            members = MemberSet(dimension=context.dimension, address=address, row_mask=new_row_mask,
                                                members=address)
                            from nanocube.context.member_context import MemberContext
                            resolved_context = MemberContext(cube=context.cube, parent=context, address=address,
                                                             row_mask=new_row_mask, member_mask=member_mask,
                                                             measure=context.measure, dimension=context.dimension,
                                                             members=members, resolve=False)
                            return True, resolved_context

            if dimension is not None and pd.api.types.is_datetime64_any_dtype(dimension.dtype):
                # 2. Date based filter expressions like "2021-01-01" or "2021-01-01 12:00:00"
                from_dt, to_dt = resolve_datetime(address)
                if (from_dt, to_dt) != (None, None):

                    # We have a valid date or data range, let's resolve it
                    from_dt, to_dt = np.datetime64(from_dt), np.datetime64(to_dt)
                    parent_row_mask = context._get_row_mask(before_dimension=context.dimension)
                    exists, new_row_mask, member_mask = dimension._check_exists_and_resolve_member(
                        member=(from_dt, to_dt), row_mask=parent_row_mask, parent_member_mask=context.member_mask,
                        skip_checks=True, evaluate_as_range=True)
                    if exists:
                        from nanocube.schema import MemberSet
                        members = MemberSet(dimension=context.dimension, address=address, row_mask=new_row_mask,
                                            members=address)
                        from nanocube.context.member_context import MemberContext
                        resolved_context = MemberContext(cube=context.cube, parent=context, address=address,
                                                         row_mask=new_row_mask, member_mask=member_mask,
                                                         measure=context.measure, dimension=context.dimension,
                                                         members=members, resolve=False)
                        return True, resolved_context

            # 3. String based filter expressions like "sales > 100" or "A, B, C"
            #    Let's try to parse the address as a Python-compliant expression from the given address
            exp: Expression = Expression(address)
            try:
                if exp.parse():
                    # We have a syntactically valid expression, so let's try to resolve/evaluate it
                    exp_resolver = ExpressionContextResolver(context, address)
                    new_context = exp.evaluate(exp_resolver)

                    if new_context is None:
                        # We have a valid expression, but it did not resolve to a context
                        context.message = (f"Failed to resolve address or expression '{address}'. "
                                           f"Maybe it tries to refer to a member name that does not exist "
                                           f"in any of the dimension of the cube.")
                        return False, context

                    if isinstance(new_context, Iterable):
                        new_context = list(new_context)[-1]
                    return True, new_context

                else:
                    # Expression parsing failed
                    context.message = f"Failed to resolve address or expression '{address}."
                    return False, context

            except ValueError as err:
                context.message = f"Failed to resolve address or expression '{address}. {err}"
                return False, context


        elif isinstance(address, dict):

            # 4. Dictionary based expressions like {"product": "A", "channel": "Online"}
            #    which are only supported for the CubeContext.
            if not isinstance(context, CubeContext):
                context.message = (f"Invalid address "
                                   f"'{address}'. Dictionary based addressing is not "
                                   f"supported for contexts representing a dimensions, members or measures.")
                return False, context

            # process all arguments of the dictionary
            for dim_name, member in address.items():
                if dim_name not in context.cube.schema.dimensions:
                    context.message = (f"Invalid address '{address}'. Dictionary key '{dim_name}' does "
                                       f"not reference to a dimension (dataframe column name) defined "
                                       f"for the cube.")
                    return False, context
                dim = context.cube.schema.dimensions[dim_name]
                # first add a dimension context...
                from nanocube.context.dimension_context import DimensionContext
                context = DimensionContext(cube=context.cube, parent=context, address=dim_name,
                                           row_mask=context.row_mask,
                                           measure=context.measure, dimension=dim, resolve=False)
                # ...then add the respective member context.
                # This approach is required 1) to be able to properly rebuild the address and 2) to
                # be able to apply the list-based member filters easily.
                context = ContextResolver.resolve(context, member, target_dimension=dim)
            return True, context


        elif isinstance(address, Iterable):
            # 5. List based expressions like ["A", "B", "C"] or (1, 2, 3)
            #    Conventions:
            #    - When applied to CubeContext: elements can be measures, dimensions or members
            #    - When applied to DimensionContext: elements can only be members of the current dimension
            #    - When applied to MemberContext: NOT SUPPORTED
            #    - When applied to MeasureContext: NOT SUPPORTED
            from nanocube.context.dimension_context import DimensionContext

            if isinstance(context, DimensionContext):
                # For increased performance, no individual upfront member checks will be made.
                # Instead, we the list as a whole will processed by numpy.
                member_mask = None
                parent_row_mask = context._get_row_mask(before_dimension=context.dimension)
                exists, new_row_mask, member_mask = (
                    context.dimension._check_exists_and_resolve_member(member=address, row_mask=parent_row_mask,
                                                                       parent_member_mask=member_mask,
                                                                       skip_checks=True))
                if not exists:
                    context.message = (f"Invalid member list '{address}'. "
                                       f"At least one member seems to be an unsupported unhashable object.")
                    return False, context

                from nanocube.schema import MemberSet
                members = MemberSet(dimension=context.dimension, address=address, row_mask=new_row_mask,
                                    members=address)
                from nanocube.context.member_context import MemberContext
                resolved_context = MemberContext(cube=context.cube, parent=context, address=address,
                                                 row_mask=new_row_mask, member_mask=member_mask,
                                                 measure=context.measure, dimension=context.dimension,
                                                 members=members, resolve=False)
                return True, resolved_context

            elif isinstance(context, CubeContext):
                # ...for CubeContext we need to check for arbitrary measures, dimensions and members one after another
                for item in address:
                    context = ContextResolver.resolve(context, item)
                return True, context

            else:
                # ...for MemberContext and MeasureContext and ContextContext we need to raise an error.
                context.message = (f"Invalid address '{address}'. List or tuple based addressing is not "
                                   f"supported for contexts representing members, measures or referenced contexts.")
                return False, context

        else:
            # for all other data types, wwe simply check if the value exists in the current dimension
            # and if so, we return a member context
            if dimension is not None:
                parent_row_mask = context._get_row_mask(before_dimension=dimension)
                exists, new_row_mask, member_mask = dimension._check_exists_and_resolve_member(address, parent_row_mask)
                if exists:
                    from nanocube.schema import Member, MemberSet
                    member = Member(dimension, address)
                    members = MemberSet(dimension=dimension, address=address, row_mask=new_row_mask,
                                        members=[member])
                    from nanocube.context.member_context import MemberContext
                    resolved_context = MemberContext(cube=context.cube, parent=context, address=address,
                                                     row_mask=new_row_mask, member_mask=member_mask,
                                                     measure=context.measure, dimension=dimension,
                                                     members=members, resolve=False)
                    return True, resolved_context

        if isinstance(address, bool):
            # This can happen if user wants to filter a context, but forgets to add an underscore
            # to the referenced context , e.g. `cube.A > 5` instead of `cube.A_ > 5` or `cube.A._ > 5`.

            context.message = (f"'{address}'(bool) is not a valid member, dimension or measure name. "
                               f"Tip: If you want to filter a context, ensure to add an underscore member name, "
                               f"e.g., as in 'cdf.sales[cdf.cost_ > 100]', otherwise would just try to filter for "
                               f"the boolean value 'True' or 'False' as a result of a value comparison "
                               f"like 'cdf.cost_ > 100'.")
        else:
            # 7. If we've not yet resolved anything meaningful, then we need to raise an error...
            context.message = (f"'{address}' is not a valid member, dimension or measure name. "
                               f"Check for typos and correct case.")
        return False, context

    @staticmethod
    def _resolve_callable(parent: Context, row_mask: np.ndarray | None,
                          measure:Measure | None, dimension: Dimension | None,
                          function: Any | None = None)   -> (bool, np.ndarray):
        if not callable(function):
            return False, row_mask

        df = parent.cube.df
        if row_mask is None:
            row_mask = parent.row_mask
        try:
            if row_mask is None:
               new_row_mask =  df[df.apply(function, axis=1)].index.to_numpy()
            else:
               new_row_mask = df.loc[row_mask].apply(function, axis=1).index.to_numpy
        except Exception as e:
            raise ValueError(f"Failed to apply filter function to dataframe. {e}")
        return True, new_row_mask

    @staticmethod
    def string_address_to_list(cube, address):
        if isinstance(address, (list, tuple)):
            return address, None

        delimiter = cube.settings.list_delimiter
        if not delimiter in address:
            return address, None
        address_tokens = address.split(delimiter)
        return address, [a.strip() for a in address_tokens]

    @staticmethod
    def merge_contexts(parent: Context, child: Context) -> Context:
        """Merges the rows of two contexts."""

        if parent.dimension == child.dimension:
            parent_row_mask = parent._get_row_mask(before_dimension=parent.dimension)
            child._member_mask = np.union1d(parent.member_mask, child.member_mask)
            child._row_mask = np.intersect1d(parent_row_mask, child._member_mask, assume_unique=True)

        else:
            child._row_mask = np.intersect1d(parent.row_mask, child._member_mask, assume_unique=True)

        return child

    @staticmethod
    def matching_data_type(address: any, dimension: Dimension) -> bool:
        """Checks if the address matches the data type of the dimension."""
        if isinstance(address, str):
            return pd.api.types.is_string_dtype(dimension.dtype)  # pd.api.types.is_object_dtype((dimension.dtype)
        elif isinstance(address, bool):
            return pd.api.types.is_bool_dtype(dimension.dtype)
        elif isinstance(address, int):
            return pd.api.types.is_integer_dtype(dimension.dtype)
        elif isinstance(address, (str, datetime.datetime, datetime.date)):
            return pd.api.types.is_datetime64_any_dtype(dimension.dtype)
        elif isinstance(address, float):
            return pd.api.types.is_float_dtype(dimension.dtype)
        return False

    @staticmethod
    def adjust_data_type(address: any, dimension: Dimension) -> any:
        """Adjusts the data type of the address to the data type of the dimension."""
        try:
            if pd.api.types.is_string_dtype(dimension.dtype):
                return str(address)
            elif pd.api.types.is_integer_dtype(dimension.dtype):
                return int(address)
            elif pd.api.types.is_datetime64_any_dtype(dimension.dtype):
                return datetime.datetime(address)
            elif pd.api.types.is_float_dtype(dimension.dtype):
                return float(address)
            elif pd.api.types.is_bool_dtype(dimension.dtype):
                if isinstance(address, bool):
                    return address
                if isinstance(address, str):
                    address = address.lower().strip()
                    return address in ["true", "t", "1", "yes", "y", "on", "1", "active", "enabled", "ok", "done"]
                    # everything else will be considered as False
                else:
                    try:
                        return bool(address)  # for other data types, we will just return the boolean value
                    except ValueError:
                        return False  # we ignore errors here. error = False
            return address
        except Exception as e:
            # just return the original address if the conversion fails, subsequent checks will be performed
            return address


class ExpressionContextResolver:
    """A helper class to provide the current context to Expressions."""

    def __init__(self, context: Context, address):
        self._context: Context | None = context
        self._address = address

    @property
    def context(self):
        return self._context

    def resolve(self, name: str) -> Context | None:
        if name == self._address:
            return None
        # Please note that the context is changing/extended every time a new context is resolved.
        self._context = self._context[name]
        return self._context
