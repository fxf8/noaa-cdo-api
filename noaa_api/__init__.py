import importlib.metadata

import noaa_api.json_schemas as json_schemas
import noaa_api.parameter_schemas as parameter_schemas

from .noaa import NOAAClient

__all__ = [
    "NOAAClient",
    "json_schemas",
    "parameter_schemas",
]

__version__ = importlib.metadata.version("noaa-api")
