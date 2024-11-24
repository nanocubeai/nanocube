"""
Copyright (c) 2024 Thomas Zeutschler. All rights reserved.

Module: logging.py
Description: Defines the logging configuration for the NanoCube package.

Author: Thomas Zeutschler
License: MIT
"""
import sys
from loguru import logger

# Logging configuration
# ...for further details please visit: https://github.com/Delgan/loguru
# *********************************************************************

# Default log level is DEBUG, to change uncomment and adjust the following lines
# logger.remove() # Remove default configuration, no logging at all
# logger.add(sys.stderr, level="INFO")

# To add additional logging to a file uncomment the following line
# logger.add("logs/nanocube_{time}.log")  # additional file based logging

# To reconfigure logger to disable asynchronous logging and log immediately to console
# Warning: This will slow down the application! Do not use in performance critical code.
# logger.remove()  # Remove default configuration
# logger.add(sys.stderr, enqueue=False, immediate=True)  # Add a synchronous console sink

