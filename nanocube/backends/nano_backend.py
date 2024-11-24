from loguru import logger
from nanocube.backends.backend import Backend

# NanoBackend Implementation
class NanoBackend(Backend):
    """
    Implementation of Backend for NanoCube data sources.
    """

    def __init__(self, cube_data: dict):
        """
        Initialize NanoBackend with cube data.

        Args:
            cube_data: A dictionary representing the NanoCube data.
        """
        self.cube_data = cube_data

    def get_members(self, dimension) -> list:
        return sorted(self.cube_data.get(dimension, []))

    def get_members_count(self, dimension) -> int:
        return len(self.get_members(dimension))

    def has_nan_members(self, dimension) -> bool:
        return None in self.cube_data.get(dimension, [])