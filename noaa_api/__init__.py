"""
NOAA Climate Data Online API Client
===================================

This module provides an asynchronous client for interacting with the NOAA National Centers for Environmental Information (NCEI) Climate Data Online (CDO) Web Services API v2.

The `NOAAClient` class manages authentication, rate limiting, and connection handling while providing methods to access all available NOAA CDO endpoints including datasets, data categories, data types, locations, stations, and the actual climate data.

Features:
---------
- Asynchronous API access using aiohttp
- Automatic rate limiting (5 requests/second, 10,000 requests/day)
- Connection pooling and management
- Strongly typed parameters and responses using Python type hints
- Comprehensive endpoint coverage for all documented NOAA CDO Web Services

Example Usage:
------
```python

import asyncio
from noaa_api.client import NOAAClient

async def main():
    # Initialize client with your NOAA API token
    client = NOAAClient(token="YOUR_NOAA_API_TOKEN")

    try:
        # Query available datasets
        datasets = await client.get_datasets(limit=10)

        # Query specific weather data
        data = await client.get_data(
            datasetid="GHCND",
            startdate="2022-01-01",
            enddate="2022-01-31",
            stationid="GHCND:USW00094728",
            limit=100
        )

        # Process the data...

    finally:
        # Close the client when done
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Notes:
------
An API token is required and can be obtained from NOAA at:
https://www.ncdc.noaa.gov/cdo-web/token
This client automatically handles the NOAA API's rate limits
For detailed API documentation, visit:
https://www.ncdc.noaa.gov/cdo-web/webservices/v2
"""  # noqa: E501

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
