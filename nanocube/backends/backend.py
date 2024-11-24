"""
NanoCube - A Python library for fast and efficient multi-dimensional data access
Copyright (c) 2024 Thomas Zeutschler. All rights reserved.

Module: backend.py
Description: Base class for NanoCube backend implementations.

Author: Thomas Zeutschler
License: MIT
"""
from abc import ABC, abstractmethod


class Backend(ABC):
    """
    Base class for NanoCube backend implementations.

    Backends are responsible for providing access to all data and metadata
    related to a single cube or table object that is accessible and queryable
    through NanoCube.

    The Backend base class defines all low level methods that need to be
    implemented by a specific backend implementation. This includes methods to
    access dimensions, members and measures as well as filtering querying and
    aggregation of data.

    Aside of NanoCubes own backend implementation, potential backends can be
    dataframe providers, like Pandas, Polars or Dask, databases, like SQLite,
    DuckDB or Postgres, or other sources that provide access to tabular data.
    """

    #region Member related methods
    @abstractmethod
    def get_members(self, dimension) -> list:
        """
        Returns a sorted list of all members for the given dimension.
        If the dimension contains NAN or NULL values, they are not included.
        Args:
            dimension: The dimension to get the members for.
        Returns:
            A sorted list of all members for the given dimension.
        """
        pass

    @abstractmethod
    def get_members_count(self, dimension) -> int:
        """
        Returns the number of members for the given dimension.
        If the dimension contains NAN or NULL values, they are not counted.
        Args:
            dimension: The dimension to get the members count for.
        Returns:
            The number of members for the given dimension.
        """
        pass

    @abstractmethod
    def has_nan_members(self, dimension) -> bool:
        """
        Returns True if the dimension contains NAN or NULL values. False otherwise.
        Args:
            dimension: The dimension to check for NAN or NULL values.
        Returns:
            True if the dimension contains NAN or NULL values. False otherwise.
        """
        pass
    #endregion
