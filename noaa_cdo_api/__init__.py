"""
NOAA Climate Data Online API Client
===================================

This module provides an asynchronous client for interacting with the NOAA National Centers for Environmental Information (NCEI) Climate Data Online (CDO) Web Services API v2.

The `NOAAClient` class manages authentication, rate limiting, and connection handling while providing methods to access all available NOAA CDO endpoints including datasets, data categories, data types, locations, stations, and the actual climate data.

Features:
---------
- Asynchronous API access using aiohttp
- Automatic rate limiting (5 requests/second, 10,000 requests/day)
- Connection pooling and TCP connection caching
- Strongly typed parameters and responses using Python type hints
- Comprehensive endpoint coverage for all documented NOAA CDO Web Services
- Proper resource management through async context managers

Example Usage:
-------------
```python
import asyncio
from noaa_cdo_api import NOAAClient, Extent

async def main():
    # Best Practice: Use async context manager for automatic resource cleanup
    async with NOAAClient(token="YOUR_TOKEN_HERE") as client:
        # Query available datasets
        datasets = await client.get_datasets(limit=10)

        # Query multiple stations in a geographic region
        stations = await client.get_stations(
            extent=Extent(40.0, -80.0, 45.0, -70.0),  # latitude_min, longitude_min, latitude_max, longitude_max
            datasetid="GHCND",
            limit=5
        )

        # Query specific weather data with unit conversion
        data = await client.get_data(
            datasetid="GHCND",
            startdate="2022-01-01",
            enddate="2022-01-31",
            stationid="GHCND:USW00094728",
            units="metric",  # Convert to metric units
            limit=100,
        )

        # Process the data...

if __name__ == "__main__":
    asyncio.run(main())
```

Important Technical Notes:
------------------------
1. Event Loop Management:
   ```python
   # ❌ BAD: Creating multiple event loops can cause issues
   loop1 = asyncio.new_event_loop()
   client1 = await NOAAClient(token="TOKEN1")
   loop2 = asyncio.new_event_loop()  # Don't do this!
   client2 = await NOAAClient(token="TOKEN2")

   # ✅ GOOD: Share the same event loop for multiple clients
   async with NOAAClient(token="TOKEN1") as client1, \
            NOAAClient(token="TOKEN2") as client2:
       # Both clients share the same event loop
       await asyncio.gather(
           client1.get_datasets(),
           client2.get_datasets()
       )
   ```

2. Resource Management:
   ```python
   # ❌ BAD: Manual resource cleanup is error-prone
   client = NOAAClient(token="YOUR_TOKEN")
   try:
       await client.get_datasets()
   finally:
       client.close()  # Might miss some resources

   # ✅ GOOD: Use async context manager
   async with NOAAClient(token="YOUR_TOKEN") as client:
       await client.get_datasets()
   # Resources are automatically cleaned up
   ```

3. Rate Limiting:
   ```python
   # ❌ BAD: Parallel requests without shared rate limiter
   async def parallel_bad():
       tasks = []
       for i in range(20):
           client = NOAAClient(token="TOKEN")  # Each has separate limiter
           tasks.append(client.get_datasets())
       return await asyncio.gather(*tasks)  # May exceed rate limits

   # ✅ GOOD: Share client for parallel requests
   async def parallel_good():
       async with NOAAClient(token="TOKEN") as client:
           tasks = [client.get_datasets() for _ in range(20)]
           return await asyncio.gather(*tasks)  # Rate limits respected
   ```

Performance Tips:
----------------
1. Connection Pooling:
   - The client maintains a pool of TCP connections
   - Reuse the same client instance for multiple requests
   - Default connection limit is 10 concurrent connections

2. Pagination:
   - Use the `limit` and `offset` parameters for large result sets
   - Consider processing data in chunks for memory efficiency

3. Data Volume:
   - Limit date ranges appropriately (1 year for daily data, 10 years for monthly)
   - Use specific station IDs when possible instead of broad geographic queries
   - Set `includemetadata=False` if metadata isn't needed

4. Caching:
   - Consider caching frequently accessed metadata (stations, datasets)
   - Implement local caching for historical data that doesn't change

For more details, see the NOAA CDO Web Services v2 documentation:
https://www.ncdc.noaa.gov/cdo-web/webservices/v2
"""  # noqa: E501

import importlib.metadata

import noaa_cdo_api.json_responses as json_responses
import noaa_cdo_api.json_schemas as json_schemas
import noaa_cdo_api.parameter_schemas as parameter_schemas

from .noaa import Extent, NOAAClient

# Assign the selected schema attributes to the json_responses module

__all__ = [
    "NOAAClient",
    "Extent",
    "json_schemas",
    "parameter_schemas",
    "json_responses",
]

__version__ = importlib.metadata.version("noaa-cdo-api")
