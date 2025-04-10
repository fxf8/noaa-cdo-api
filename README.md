# NOAA Climate Data Online API Client

[![GitHub Actions](https://github.com/FuexFollets/noaa-api/actions/workflows/lint.yml/badge.svg)](https://github.com/FuexFollets/noaa-api/actions)
[![Python Version](https://img.shields.io/pypi/pyversions/noaa-api.svg)](https://pypi.org/project/noaa-api/)
[![PyPI version](https://badge.fury.io/py/noaa-api.svg)](https://badge.fury.io/py/noaa-api)
[![License](https://img.shields.io/github/license/FuexFollets/noaa-api.svg)](https://github.com/FuexFollets/noaa-api/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-pdoc-blue)](https://fuexfollets.github.io/noaa-api)
[![Lint](https://img.shields.io/badge/docs-pdoc-blue)](https://fuexfollets.github.io/noaa-api)
<!-- [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) -->

An asynchronous Python client for the NOAA National Centers for Environmental Information (NCEI) Climate Data Online (CDO) Web Services API v2. Features automatic rate limiting, connection pooling, and comprehensive type safety.

## Features

- ⚡ **Asynchronous API**: Built with `aiohttp` for high-performance async I/O
- 🚦 **Automatic Rate Limiting**: Enforces NOAA's limits (5 req/sec, 10,000 req/day)
- 🔄 **Connection Pooling**: Efficient TCP connection reuse
- 📝 **Type Safety**: Full type hints and runtime validation
- 🎨 **Beautiful Documentation**: Color-formatted docstrings with pdoc
- 🛡️ **Resource Management**: Proper async context management
- 📊 **Complete Coverage**: All NOAA CDO v2 endpoints supported

## Installation

```bash
pip install noaa-api
```

## Quick Start

```python
import asyncio
from noaa_api import NOAAClient

async def main():
    # Best Practice: Use async context manager for automatic cleanup
    async with NOAAClient(token="YOUR_TOKEN_HERE") as client:
        # Query available datasets
        datasets = await client.get_datasets(limit=10)
        
        # Query stations in a geographic region
        stations = await client.get_stations(
            extent="42.0,-90.0,40.0,-88.0",  # north,west,south,east
            datasetid="GHCND",
            limit=5
        )
        
        # Get climate data with unit conversion
        data = await client.get_data(
            datasetid="GHCND",
            startdate="2022-01-01",
            enddate="2022-01-31",
            stationid="GHCND:USW00094728",
            units="metric",
            limit=100,
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## Important Implementation Notes

### Event Loop Management
```python
# ❌ BAD: Creating multiple event loops
loop1 = asyncio.new_event_loop()
client1 = await NOAAClient(token="TOKEN1")
loop2 = asyncio.new_event_loop()  # Don't do this!

# ✅ GOOD: Share the same event loop
async with NOAAClient(token="TOKEN1") as client1, \
         NOAAClient(token="TOKEN2") as client2:
    await asyncio.gather(
        client1.get_datasets(),
        client2.get_datasets()
    )
```

### Resource Management
```python
# ❌ BAD: Manual cleanup
client = NOAAClient(token="TOKEN")
try:
    await client.get_datasets()
finally:
    client.close()  # Might miss resources

# ✅ GOOD: Use async context manager
async with NOAAClient(token="TOKEN") as client:
    await client.get_datasets()
```

### Rate Limiting
```python
# ❌ BAD: Parallel requests with separate limiters
async def parallel_bad():
    tasks = []
    for i in range(20):
        client = NOAAClient(token="TOKEN")  # Each has separate limiter
        tasks.append(client.get_datasets())
    return await asyncio.gather(*tasks)  # May exceed limits

# ✅ GOOD: Share client for parallel requests
async def parallel_good():
    async with NOAAClient(token="TOKEN") as client:
        tasks = [client.get_datasets() for _ in range(20)]
        return await asyncio.gather(*tasks)  # Rate limits respected
```

## Performance Tips

1. **Connection Pooling**
   - Reuse the same client instance
   - Default connection limit is 10
   - Adjust with `tcp_connector_limit` parameter

2. **Pagination**
   - Use `limit` and `offset` for large result sets
   - Process data in chunks for memory efficiency

3. **Data Volume**
   - Limit date ranges (1 year for daily, 10 years for monthly)
   - Use specific station IDs when possible
   - Set `includemetadata=False` if not needed

4. **Caching**
   - Cache frequently accessed metadata
   - Implement local caching for historical data

## API Documentation

Full API documentation with colored formatting is available at [https://fuexfollets.github.io/noaa-api](https://fuexfollets.github.io/noaa-api).

### Available Endpoints

- `/datasets`: Query available datasets
- `/datacategories`: Query data categories
- `/datatypes`: Query data types
- `/locationcategories`: Query location categories
- `/locations`: Query locations
- `/stations`: Query weather stations
- `/data`: Query actual climate data

## Type Safety

The library provides comprehensive type checking through:
- `TypedDict` schemas for all parameters
- Runtime validation of parameter values
- Proper enum types for constrained fields

Example with type checking:
```python
from noaa_api import parameter_schemas

params: parameter_schemas.StationsParameters = {
    "extent": "42.0,-90.0,40.0,-88.0",
    "datasetid": "GHCND",
    "limit": 100
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- NOAA's National Centers for Environmental Information (NCEI)
- The aiohttp team for their excellent HTTP client
- Contributors to the project

## Getting Help

- [Open an issue](https://github.com/FuexFollets/noaa-api/issues)
- [Read the docs](https://fuexfollets.github.io/noaa-api)
- [NOAA CDO API Documentation](https://www.ncdc.noaa.gov/cdo-web/webservices/v2)
