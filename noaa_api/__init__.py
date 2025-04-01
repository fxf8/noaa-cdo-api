import importlib.metadata

import json_schemas
import parameter_schemas

from .noaa import NOAAClient

__all__ = [
    "NOAAClient",
    "json_schemas",
    "parameter_schemas",
]

__version__ = importlib.metadata.version("noaa-api")
