
import pandas as pd
from nanocube.backends.backend import Backend


# PandasBackend Implementation
class PandasBackend(Backend):
    """
    Implementation of Backend for Pandas DataFrames.
    """
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize PandasBackend with a DataFrame.

        Args:
            dataframe: A pandas DataFrame object.
        """
        self.dataframe = dataframe

    def get_members(self, dimension) -> list:
        if dimension not in self.dataframe.columns:
            raise ValueError(f"Dimension '{dimension}' not found in DataFrame.")
        return sorted(self.dataframe[dimension].dropna().unique())

    def get_members_count(self, dimension) -> int:
        return len(self.get_members(dimension))

    def has_nan_members(self, dimension) -> bool:
        if dimension not in self.dataframe.columns:
            raise ValueError(f"Dimension '{dimension}' not found in DataFrame.")
        return self.dataframe[dimension].isna().any()
