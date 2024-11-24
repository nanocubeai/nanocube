"""
NanoCube - A Python library for fast and efficient multi-dimensional data access
Copyright (c) 2024 Thomas Zeutschler. All rights reserved.

Module: backend
Description: Factory class to create Backend instances dynamically.
Author: Thomas Zeutschler
License: MIT
"""
from loguru import logger
import pandas as pd

from nanocube.backends.backend import Backend
from nanocube.backends.nano_backend import NanoBackend
from nanocube.backends.pandas_backend import PandasBackend


# Factory Class
class BackendFactory:
    """
    Factory class to create Backend instances dynamically.
    """

    @staticmethod
    def create_backend(backend_type: str, **kwargs) -> Backend:
        """
        Creates an instance of the requested backend type.

        Args:
            backend_type: The type of backend to create (e.g., 'nano', 'pandas').
            kwargs: Arguments specific to the backend type.
        Returns:
            An instance of the requested backend.
        """
        if backend_type == "nano":
            if "cube_data" not in kwargs:
                logger.error("Missing 'cube_data' argument for NanoBackend.")
                raise ValueError("Missing 'cube_data' argument for NanoBackend.")
            return NanoBackend(kwargs["cube_data"])

        elif backend_type == "pandas":
            if "dataframe" not in kwargs:
                logger.error("Missing 'dataframe' argument for PandasBackend.")
                raise ValueError("Missing 'dataframe' argument for PandasBackend.")
            return PandasBackend(kwargs["dataframe"])

        else:
            logger.error(f"Unknown backend type requested: {backend_type}")
            raise ValueError(f"Unknown backend type: {backend_type}")


# Example Usage
if __name__ == "__main__":
    # Example NanoBackend
    nano_data = {"dimension1": ["a", "b", None, "c"], "dimension2": [1, 2, 3, None]}
    nano_backend = BackendFactory.create_backend("nano", cube_data=nano_data)
    print("NanoBackend Members:", nano_backend.get_members("dimension1"))
    print("NanoBackend Has NAN Members:", nano_backend.has_nan_members("dimension1"))

    # Example PandasBackend
    df = pd.DataFrame({
        "dimension1": ["a", "b", None, "c"],
        "dimension2": [1, 2, 3, None]
    })
    pandas_backend = BackendFactory.create_backend("pandas", dataframe=df)
    print("PandasBackend Members:", pandas_backend.get_members("dimension1"))
    print("PandasBackend Has NAN Members:", pandas_backend.has_nan_members("dimension1"))