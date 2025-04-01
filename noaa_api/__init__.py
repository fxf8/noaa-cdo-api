import importlib.metadata

import noaa_api.json_responses as json_responses
import noaa_api.json_schemas as json_schemas
import noaa_api.parameter_schemas as parameter_schemas

from .noaa import NOAAClient

# Assign the selected schema attributes to the json_responses module

__all__ = [
    "NOAAClient",
    "json_schemas",
    "parameter_schemas",
    "json_responses",
]

__version__ = importlib.metadata.version("noaa-api")
