# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pandas.api.types import is_numeric_dtype
from pandas.core.dtypes.common import is_bool_dtype

from nanocube.common import pythonize
from nanocube.schema import Dimension
from nanocube.schema import DimensionCollection
from nanocube.schema import Measure
from nanocube.schema import MeasureCollection
from nanocube.settings import CachingStrategy


class Schema:
    """
    Defines a schema for multi-dimensional data access through a CubedPandas cube upon an
    underlying Pandas dataframe.

    A schema defines the dimensions and measures of the cube and can be either automatically inferred
    from the underlying Pandas dataframe or defined explicitly.
    """

    def __init__(self, df: pd.DataFrame | None = None, schema: Any = None,
                 caching: CachingStrategy = CachingStrategy.LAZY):
        """
        Initializes a schema for a CubedPandas cube upon a given Pandas dataframe. If the argument `schema`,
        either a JSON string or a python dictionary or a file name containing valid schema information,
        is not provided, a default schema will be inferred from the Pandas dataframe.

         Args:
            df: (optional) the Pandas dataframe to build the schema from or for.

            schema: (optional) a schema to initialize the Schema with. The parameter `schema` can either be
                another Schema object, a Python dictionary containing valid schema information, a json string
                containing valid schema information or a file name or path to a json file containing valid schema
                information.
        """
        self._df: pd.DataFrame | None = df
        self._schema: dict = self._load_schema(schema)
        self._dimensions: DimensionCollection = DimensionCollection()
        self._measures: MeasureCollection = MeasureCollection()
        self._caching: CachingStrategy = caching
        self._validation_message: str = ""

        if schema is not None:
            if not self._validate_and_create():
                raise ValueError(self._validation_message)

    def _load_schema(self, schema: Any) -> dict:
        if schema is None:
            return {"dimensions": [], "measures": []}
        if isinstance(schema, dict):
            return schema
        if isinstance(schema, str):
            try:
                schema_dict = json.loads(schema)
            except ValueError as err:
                try:
                    with open(schema, 'r') as file:
                        return json.load(file)
                except FileNotFoundError:
                    raise ValueError("Invalid schema information.")

    def _validate_and_create(self) -> bool:
        """
        Validates the schema against the given Pandas dataframe and creates the dimensions and measures.

        Returns:
        True, if the schema is valid for the given Pandas dataframe.
        Otherwise, False and a validation message `_validation_message` is set.
        """
        df = self._df

        # if defined in the schema, override the default caching strategy
        if "caching" in self._schema:
            self._caching = CachingStrategy.from_any(self._schema["caching"])

        # get dimension and measure columns from the schema
        self._dimensions = DimensionCollection()
        for dimension in self._schema["dimensions"]:
            if "column" in dimension:
                column = dimension["column"]
                if column not in df.columns:
                    self._validation_message = f"Dimension column '{column}' not found in dataframe."
                    return False
                alias_name = None

                if "alias" in dimension:
                    alias_name = dimension["alias"]

                caching = self._caching
                dim_specific_caching = False
                if "caching" in dimension:
                    caching = CachingStrategy.from_any(dimension["caching"])
                    dim_specific_caching = True

                self._dimensions.add(Dimension(df, column=column, alias=alias_name,
                                               caching=caching, dim_specific_caching=dim_specific_caching))
            else:
                if isinstance(dimension, str) or isinstance(dimension, int):
                    if dimension not in df.columns:
                        self._validation_message = f"Dimension column named '{dimension}' not found in dataframe."
                        return False
                    self._dimensions.add(Dimension(df, column=dimension, alias=None, caching=self._caching))
                else:
                    self._validation_message = f"Dimension column of type '{type(dimension)}' not found in schema."
                    return False

        self._measures = MeasureCollection()
        for measure in self._schema["measures"]:
            if "column" in measure:
                column = measure["column"]
                if column not in df.columns:
                    self._validation_message = f"Measure column named '{column}' not found in dataframe."
                    return False
                alias_name = None
                if "alias" in measure:
                    alias_name = measure["alias"]

                self._measures.add(Measure(df, column=column, alias=alias_name))
            else:
                if isinstance(measure, str) or isinstance(measure, int):
                    if measure not in df.columns:
                        self._validation_message = f"Measure column '{measure}' not found in dataframe."
                        return False
                    number_format = None
                    if "numberFormat" in measure:
                        number_format = measure["numberFormat"]

                    self._measures.add(Measure(df, column=measure, alias=None, number_format=number_format))
                else:
                    self._validation_message = f"Measure column of type '{type(measure)}' not found in schema."
                    return False
        return True

    @property
    def dimensions(self) -> DimensionCollection:
        """ Returns the dimensions of the schema."""
        return self._dimensions

    @property
    def measures(self) -> MeasureCollection:
        """ Returns the measures of the schema."""
        return self._measures

    def infer_schema(self, exclude: str | list | tuple | None = None) -> Schema:
        """
        Infers a multidimensional schema from the Pandas dataframe of the Schema or another Pandas dataframe by
        analyzing the columns of the table and their contents.

        This process can be time-consuming for large tables. For such cases, it is recommended to
        infer the schema only from a sample of the records by setting parameter 'sample_records' to True.
        By default, the schema is inferred from and validated against all records.

        The inference process tries to identify the dimensions and their hierarchies of the cube as
        well as the measures of the cube. If no schema cannot be inferred, an exception is raised.

        By default, string, datetime and boolean columns are assumed to be measure columns and
        numerical columns are assumed to be measures for cube computations. By default, all columns
        of the Pandas dataframe will be used to infer the schema. However, a subset of columns can be
        specified to infer the schema from. The subset needs to contain at least two columns, one
        for a single dimensions and one for a single measures.

        For more complex tables it is possible or even likely that the resulting schema does not match your
        expectations or requirements. For such cases, you will need to build your schema manually.
        Please refer the documentation for further details on how to build a schema manually.

        :param exclude: (optional) a list of either column names or ordinal column ids to exclude when
            inferring the schema.

        :return: Returns the inferred schema.
        """
        df = self._df
        schema_dict = {"dimensions": [], "measures": []}
        self._dimensions = DimensionCollection()
        self._measures = MeasureCollection()
        aliases: dict[str, str] = {}

        if exclude is not None:
            if isinstance(exclude, str) or isinstance(exclude, int):
                exclude = [exclude,]
        else:
            exclude = []

        for column_name, dtype in df.dtypes.items():
            column_name = str(column_name)
            if column_name not in exclude:
                dict_column = {"column": column_name}

                # check if the column name is a valid Python identifier
                if not column_name.isidentifier():
                    # ...it's not a valid Python identifier, lets try to create a valid alias
                    alias = pythonize(column_name)
                    if alias.isidentifier() and alias not in aliases:
                        # check if the alias is not already in use, to prohibit duplicates
                        aliases[column_name] = alias
                        dict_column["alias"] = alias

                if is_numeric_dtype(df[column_name]) and not is_bool_dtype(df[column_name]):
                    schema_dict["measures"].append(dict_column)
                    self._measures.add(Measure(df, column_name))
                else:
                    schema_dict["dimensions"].append(dict_column)
                    self._dimensions.add(Dimension(df, column=column_name, alias=None, caching=self._caching))

        return self

    # # region Serialization

    def to_dict(self) -> dict:
        """
        Converts the schema into a dictionary containing schema information for an Cube.

        :return: Returns a dictionary containing the schema information.
        """
        schema = {"caching": self._caching.name,
                  "dimensions": [],
                  "measures": []}
        for measure in self._measures:
            schema["measures"].append(measure.to_dict())
        for dimension in self._dimensions:
            schema["dimensions"].append(dimension.to_dict())
        return schema

    def to_json(self) -> str:
        """
        Converts the schema into a dictionary containing schema information for an Cube.

        :return: Returns a dictionary containing the schema information.
        """
        return json.dumps(self.to_dict)

    def save_as_json(self, file_name: str):
        """
        Saves the schema as a json file.

        :param file_name: The name of the file to save the schema to.
        """
        with open(file_name, 'w') as file:
            json.dump(self.to_dict(), file)

    # endregion

    def __str__(self) -> str:
        return self.to_json()

    def __repr__(self) -> str:
        return self.to_json()

    def __len__(self):
        """ Returns the number of dimensions of the schema."""
        return len(self.dimensions)

