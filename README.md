# NOAA Climate Data Online API Client

<!-- [![Python Version](https://img.shields.io/pypi/pyversions/noaa-cdo-api.svg)](https://pypi.org/project/noaa-cdo-api/) -->
[![PyPI version](https://badge.fury.io/py/noaa-cdo-api.svg)](https://badge.fury.io/py/noaa-cdo-api)
[![GitHub Actions](https://github.com/fxf8/noaa-cdo-api/actions/workflows/lint.yml/badge.svg)](https://github.com/fxf8/noaa-cdo-api/actions)
[![License](https://img.shields.io/github/license/fxf8/noaa-cdo-api.svg)](https://github.com/fxf8/noaa-cdo-api/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-pdoc-blue)](https://fxf8.github.io/noaa-cdo-api)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
<!-- [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) -->

An asynchronous Python client for the NOAA National Centers for Environmental Information (NCEI) Climate Data Online (CDO) Web Services API v2. Features automatic rate limiting, connection pooling, and comprehensive type safety.

## Features

- ⚡ **Asynchronous API**: Built with `aiohttp` for high-performance async I/O
- 🚦 **Automatic Rate Limiting**: Enforces NOAA's limits (5 req/sec, 10,000 req/day)
- 🔄 **Connection Pooling**: Efficient TCP connection reuse
- 📝 **Type Safety**: Full type hints and runtime validation
- 🎨 **Beautiful Documentation**: Color-formatted docstrings with pdoc
- 🛡️ **Resource Management**: Proper async context management
- 📊 **Complete Coverage**: All documented NOAA CDO v2 endpoints supported

## Why this library

Working with NOAA's CDO API in Python usually means one of three things. Here's how they compare:

| | `noaa-cdo-api` | Other CDO Python wrappers | Roll your own (`aiohttp`/`requests`) |
|---|---|---|---|
| Async / concurrent requests | ✅ `aiohttp`-native | Usually ❌ (sync-only) | Depends |
| Rate limiting (5/sec, 10k/day) built in | ✅ enforced automatically | ❌ caller manages | ❌ caller manages |
| Typed responses (`TypedDict` per endpoint) | ✅ full editor autocomplete | ❌ `dict[str, Any]` / DataFrame | ❌ |
| Ships `py.typed` marker | ✅ | Rarely | N/A |
| Connection pooling | ✅ (aiohttp `TCPConnector`) | Partial | You wire it |
| Loop-aware session reuse | ✅ (auto rebuild on loop change) | N/A | Manual |
| All v2 endpoints covered | ✅ | Varies | N/A |

**The unique value: async + rate-limit-aware + typed in one package.** You can `asyncio.gather()` a hundred requests without worrying about blacklisting, and your IDE can autocomplete `response["results"][0]["value"]` all the way down.

## Installation

```bash
pip install noaa-cdo-api
```

## API Documentation

Full API documentation with colored formatting is available at [https://fxf8.github.io/noaa-cdo-api/](https://fxf8.github.io/noaa-cdo-api/).

## Quick Start

```python
import asyncio
from noaa_cdo_api import NOAAClient, Extent

async def main():
    # Best Practice: Use async context manager for automatic cleanup
    async with NOAAClient(token="YOUR_TOKEN_HERE") as client:
        # Query available datasets
        datasets = await client.get_datasets(limit=10)

        # Query stations in a geographic region
        stations = await client.get_stations(
            extent=Extent(40.0, -80.0, 45.0, -75.0), # latitude_min, longitude_min, latitude_max, longitude_max
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
client1 = await NOAAClient(token="TOKEN1")
client2 = await NOAAClient(token="TOKEN2")

results = [*asyncio.run(client1.get_datasets(...)), *asyncio.run(client2.get_datasets(...))]

# ✅ GOOD: Share the same event loop (note that rate limits apply **per token**)
async with NOAAClient(token="TOKEN1") as client1, \
         NOAAClient(token="TOKEN2") as client2:
    await asyncio.gather(
        client1.get_datasets(),
        client2.get_datasets()
    )
```

### Resource Management
```python
# ❌ Less ideal but functional: Manual cleanup
client = NOAAClient(token="TOKEN")
try:
    await client.get_datasets()
finally:
    await client.close()

# ✅ Better: Use async context manager
async with NOAAClient(token="TOKEN") as client:
    await client.get_datasets()
```

### Rate Limiting
```python
# ✅ Good: Use only a single client
async def parallel_with():
    async with NOAAClient(token="TOKEN") as client:
        tasks = [client.get_datasets() for _ in range(20)]
        return await asyncio.gather(*tasks)  # Rate limits respected


# ❌ Bad: Each client has separate rate limits
async def parallel_separate():
    tasks = []
    for i in range(20):
        client = NOAAClient(token="TOKEN")  # Each has separate limiter
        tasks.append(client.get_datasets())
    return await asyncio.gather(*tasks)  # May exceed rate limits

```

## Design Decisions

Three questions shaped the architecture. The tradeoffs are called out honestly so you can decide if this library's opinions match yours.

### Why async, and why bake in rate limiting?

Climate data pulls are I/O-bound and often bulk (many stations × many years). Doing them sequentially wastes real time — but naive concurrency hits NOAA's rate limits fast (5 req/sec, 10,000 per day), and repeated violations can get a token blacklisted.

The library uses two `aiolimiter.AsyncLimiter` instances — one per-second, one per-day — combined via `async with` on every request. Result:

- `await asyncio.gather(*many_requests)` is safe; the limiter enforces spacing transparently
- Both limits are respected simultaneously without user code
- Rate limiting is a *property of the client*, not a discipline the caller has to remember

**Tradeoff:** limits are enforced *per client instance*. Sharing one client across a task group is the correct pattern; spinning up a new client per request defeats the purpose. This is documented in the Rate Limiting section above.

### Why `TypedDict` for every response?

Most Python API wrappers return `dict[str, Any]` (or a DataFrame that erases the schema). Both throw away everything the API contract tells us — field names, value types, which fields are optional.

Every endpoint here returns a `TypedDict` matching the CDO response shape (`DatasetsJSON`, `StationsJSON`, `DataJSON`, ...). In a Pyright/mypy-aware editor:

- Autocomplete works down to individual response fields
- Typos in field access are caught at edit time, not at runtime on a 3 AM cron job
- Refactoring across a codebase is safe

**Tradeoff:** NOAA returns a different shape on rate-limit-exceeded responses, so return types are `SuccessJSON | RateLimitJSON` unions. Callers narrow with `isinstance` or a key check before touching fields. The plan for a future release is to raise `RateLimitError` instead, so the happy path returns a single concrete type.

### Why loop-aware session reuse?

`aiohttp.ClientSession` is bound to the event loop that created it — reusing one across loops fails in confusing ways. Realistic scenarios where that happens: pytest with `asyncio_mode`, notebook re-runs, embedding in a larger app that owns its own loop.

The client tracks which loop owns its `TCPConnector` and `ClientSession` in a private `_session_loop` attribute set at session creation. When a request arrives on a different loop, the connector and session are rebuilt automatically. Critically, this is done **without reading any aiohttp private attributes** — earlier revisions of the code peeked at `session._loop`, which is not part of aiohttp's public API and would silently break on upgrades. The current implementation only uses `asyncio.get_running_loop()` and object identity.

**Tradeoff:** one identity comparison per request, and a bit of internal state. Worth it for correctness in the "reused across contexts" case.

## Tips

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
from noaa_cdo_api import parameter_schemas

params: parameter_schemas.StationsParameters = {
    "extent": "42.0,-90.0,40.0,-88.0",
    "datasetid": "GHCND",
    "limit": 100
}
```
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- NOAA's National Centers for Environmental Information (NCEI)
- The aiohttp team for their excellent HTTP client
- Contributors to the project

## Getting Help

- [Open an issue](https://github.com/fxf8/noaa-cdo-api/issues)
- [Read the docs](https://fxf8.github.io/noaa-cdo-api)
- [NOAA CDO API Documentation](https://www.ncdc.noaa.gov/cdo-web/webservices/v2)
