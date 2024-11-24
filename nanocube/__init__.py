"""
NanoCube - A Python library for fast and efficient multi-dimensional data access
Copyright (c) 2024 Thomas Zeutschler. All rights reserved.

Module: __init__.py
Description: Library initialization.

Author: Thomas Zeutschler
License: MIT
"""
from loguru import logger

import nanocube.context as context
from nanocube.common import cubed
from nanocube.ambiguities import Ambiguities
from nanocube.context.context import Context
from nanocube.context.context_context import ContextContext
from nanocube.context.cube_context import CubeContext
from nanocube.context.enums import ContextFunction, ContextAllocation, BooleanOperation
from nanocube.context.filter_context import FilterContext
from nanocube.context.function_context import FunctionContext
from nanocube.context.measure_context import MeasureContext
from nanocube.context.member_context import MemberContext
from nanocube.context.member_not_found_context import MemberNotFoundContext
from nanocube.cube import Cube
from nanocube.schema.dimension import Dimension
from nanocube.schema.dimension_collection import DimensionCollection
from nanocube.schema.measure import Measure
from nanocube.schema.measure_collection import MeasureCollection
from nanocube.schema.member import Member, MemberSet
from nanocube.schema.schema import Schema
from nanocube.settings import CachingStrategy

from nanocube.nano import NanoCube
from nanocube.nano import NanoIndex


__author__ = "Thomas Zeutschler"
__version__ = "0.2.1"
__license__ = "MIT"
VERSION = __version__

logger.info(f"NanoCube package version {__version__} initialized.")

__all__ = [
    "NanoCube",
    "NanoIndex",

    "Ambiguities",
    "BooleanOperation",
    "CachingStrategy",
    "context",
    "Context",
    "ContextAllocation",
    "ContextContext",
    "ContextFunction",
    "CubeContext",
    "Cube",
    "cubed",
    "Dimension",
    "DimensionCollection",
    "FilterContext",
    "FunctionContext",
    "Measure",
    "MeasureCollection",
    "MeasureContext",
    "Member",
    "MemberContext",
    "MemberNotFoundContext",
    "MemberSet",
    "Schema",
]