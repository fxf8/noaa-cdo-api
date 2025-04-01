from collections.abc import Mapping
from typing import ClassVar, cast

import aiohttp
import aiolimiter

import noaa_api.json_schemas as json_schemas
import noaa_api.parameter_schemas as parameter_schemas

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
- Comprehensive endpoint coverage for all NOAA CDO Web Services

Usage:
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
Notes:

An API token is required and can be obtained from NOAA at:
https://www.ncdc.noaa.gov/cdo-web/token
This client automatically handles the NOAA API's rate limits
For detailed API documentation, visit:
https://www.ncdc.noaa.gov/cdo-web/webservices/v2
"""  # noqa: E501


class NOAAClient:
    """
    Asynchronous client for accessing the NOAA NCEI Climate Data Online (CDO) Web API v2.

    This client handles API authentication, rate limiting, connection management, and
    provides methods to query all available NOAA CDO endpoints.

    Attributes:
        token (str): The API token for authentication with NOAA API.
        tcp_connector (aiohttp.TCPConnector): TCP connector for managing HTTP connections.
        aiohttp_session (aiohttp.ClientSession): Session for making HTTP requests.
        seconds_request_limiter (aiolimiter.AsyncLimiter): Limiter for requests per second (5 req/sec).
        daily_request_limiter (aiolimiter.AsyncLimiter): Limiter for requests per day (10,000 req/day).
        ENDPOINT (ClassVar[str]): Base URL for the NOAA CDO API v2.

    Methods:
        get_datasets: Query information about available datasets.
        get_data_categories: Query information about data categories.
        get_datatypes: Query information about data types.
        get_location_categories: Query information about location categories.
        get_locations: Query information about locations.
        get_stations: Query information about weather stations.
        get_data: Query actual climate data based on specified parameters.
        close: Close the aiohttp session.

    Notes:
        - All query methods are asynchronous and return parsed JSON responses.
        - The client automatically enforces NOAA's API rate limits (5 req/sec, 10,000 req/day).
        - For ID-based queries, pass the ID as the first parameter.
        - For broader queries, use the keyword parameters to filter results.
    """  # noqa: E501

    __slots__: tuple[str, ...] = (
        "token",
        "tcp_connector",
        "aiohttp_session",
        "seconds_request_limiter",
        "daily_request_limiter",
    )

    token: str
    tcp_connector: aiohttp.TCPConnector
    aiohttp_session: aiohttp.ClientSession

    seconds_request_limiter: aiolimiter.AsyncLimiter
    daily_request_limiter: aiolimiter.AsyncLimiter

    ENDPOINT: ClassVar[str] = "https://www.ncei.noaa.gov/cdo-web/api/v2"

    def __init__(
        self,
        token: str,
        tcp_connector_limit: int = 10,
        keepalive_timeout: int = 60,  # Seconds
    ):
        """
        Initialize the NOAA API client.

        Args:
            token (str): The API token for authentication with NOAA API.
            tcp_connector_limit (int, optional): Maximum number of connections. Defaults to 10.
            keepalive_timeout (int, optional): Timeout for keeping connections alive in seconds. Defaults to 60.
        """  # noqa: E501

        self.token = token
        self.tcp_connector = aiohttp.TCPConnector(
            limit=tcp_connector_limit, keepalive_timeout=keepalive_timeout
        )

        self.aiohttp_session = aiohttp.ClientSession(
            headers={"token": self.token}, connector=self.tcp_connector
        )

        self.seconds_request_limiter = aiolimiter.AsyncLimiter(
            5,  # 5 requests per second
            1,  # 1 second
        )

        self.daily_request_limiter = aiolimiter.AsyncLimiter(
            10_000,  # 10_000 requests per day
            60 * 60 * 24,  # 1 day
        )

    async def _make_request(
        self, url: str, parameters: parameter_schemas.AnyParameter | None = None
    ) -> aiohttp.ClientResponse:
        """
        Internal method to make a rate-limited API request.

        Args:
            url (str): The API endpoint URL.
            parameters (parameter_schemas.AnyParameter | None, optional): Query parameters. Defaults to None.

        Returns:
            aiohttp.ClientResponse: The HTTP response object.

        Raises:
            ValueError: If 'limit' parameter exceeds 1000.
            aiohttp.ClientResponseError: If the request fails.
        """  # noqa: E501

        if (
            parameters is not None
            and "limit" in parameters
            and parameters["limit"] > 1000
        ):
            raise ValueError("Parameter 'limit' must be less than or equal to 1000")

        async with (
            self.seconds_request_limiter,
            self.daily_request_limiter,
            self.aiohttp_session.get(
                url, params=cast(Mapping[str, str], parameters)
            ) as response,
        ):
            response.raise_for_status()
            return response

    async def get_datasets(
        self,
        id: str | None = None,
        *,
        datatypeid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        startdate: str = "",  # YYYY-MM-DD
        enddate: str = "",  # YYYY-MM-DD
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.DatasetsJSON | json_schemas.RateLimitJSON:
        """
        Query information about available datasets.

        Args:
            id (str | None, optional): Specific dataset ID to retrieve. Defaults to None.
            datatypeid (str | list[str], optional): Filter by data type ID(s). Defaults to "".
            locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
            stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
            startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
            enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
            sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
            sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
            limit (int, optional): Maximum number of results to return. Defaults to 25.
            offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
            json_schemas.DatasetsJSON | json_schemas.RateLimitJSON: Dataset information or rate limit message.
        """  # noqa: E501

        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/datasets"
            if id is None
            else f"{self.ENDPOINT}/datasets/{id}",
            parameters={
                "datatypeid": "&".join(datatypeid)
                if isinstance(datatypeid, list)
                else datatypeid,
                "locationid": "&".join(locationid)
                if isinstance(locationid, list)
                else locationid,
                "stationid": "&".join(stationid)
                if isinstance(stationid, list)
                else stationid,
                "startdate": startdate,
                "enddate": enddate,
                "sortfield": sortfield,
                "sortorder": sortorder,
                "limit": limit,
                "offset": offset,
            },
        )

        return cast(
            json_schemas.DatasetsJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_data_categories(
        self,
        id: str | None = None,
        *,
        datasetid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        startdate: str = "",  # YYYY-MM-DD
        enddate: str = "",  # YYYY-MM-DD
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON:
        """
        Query information about data categories.

        Args:
            id (str | None, optional): Specific data category ID to retrieve. Defaults to None.
            datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
            locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
            stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
            startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
            enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
            sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
            sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
            limit (int, optional): Maximum number of results to return. Defaults to 25.
            offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
            json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON: Data category information or rate limit message.
        """  # noqa: E501

        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/datacategories"
            if id is None
            else f"{self.ENDPOINT}/datacategories/{id}",
            parameters={
                "datasetid": "&".join(datasetid)
                if isinstance(datasetid, list)
                else datasetid,
                "locationid": "&".join(locationid)
                if isinstance(locationid, list)
                else locationid,
                "stationid": "&".join(stationid)
                if isinstance(stationid, list)
                else stationid,
                "startdate": startdate,
                "enddate": enddate,
                "sortfield": sortfield,
                "sortorder": sortorder,
                "limit": limit,
                "offset": offset,
            },
        )

        return cast(
            json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_datatypes(
        self,
        id: str | None = None,
        *,
        datasetid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        startdate: str = "",  # YYYY-MM-DD
        enddate: str = "",  # YYYY-MM-DD
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.DatatypesJSON | json_schemas.RateLimitJSON:
        """
        Query information about data types.

        Args:
            id (str | None, optional): Specific data type ID to retrieve. Defaults to None.
            datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
            locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
            stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
            startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
            enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
            sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
            sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
            limit (int, optional): Maximum number of results to return. Defaults to 25.
            offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
            json_schemas.DatatypesJSON | json_schemas.RateLimitJSON: Data type information or rate limit message.
        """  # noqa: E501

        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/datatypes"
            if id is None
            else f"{self.ENDPOINT}/datatypes/{id}",
            parameters={
                "datasetid": "&".join(datasetid)
                if isinstance(datasetid, list)
                else datasetid,
                "locationid": "&".join(locationid)
                if isinstance(locationid, list)
                else locationid,
                "stationid": "&".join(stationid)
                if isinstance(stationid, list)
                else stationid,
                "startdate": startdate,
                "enddate": enddate,
                "sortfield": sortfield,
                "sortorder": sortorder,
                "limit": limit,
                "offset": offset,
            },
        )

        return cast(
            json_schemas.DatatypesJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_location_categories(
        self,
        id: str | None = None,
        *,
        datasetid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        startdate: str = "",  # YYYY-MM-DD
        enddate: str = "",  # YYYY-MM-DD
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON:
        """
        Query information about location categories.

        Args:
            id (str | None, optional): Specific location category ID to retrieve. Defaults to None.
            datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
            locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
            stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
            startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
            enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
            sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
            sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
            limit (int, optional): Maximum number of results to return. Defaults to 25.
            offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
            json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON: Location category information or rate limit message.
        """  # noqa: E501
        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/locationcategories"
            if id is None
            else f"{self.ENDPOINT}/locationcategories/{id}",
            parameters={
                "datasetid": "&".join(datasetid)
                if isinstance(datasetid, list)
                else datasetid,
                "locationid": "&".join(locationid)
                if isinstance(locationid, list)
                else locationid,
                "stationid": "&".join(stationid)
                if isinstance(stationid, list)
                else stationid,
                "startdate": startdate,
                "enddate": enddate,
                "sortfield": sortfield,
                "sortorder": sortorder,
                "limit": limit,
                "offset": offset,
            },
        )

        return cast(
            json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_locations(
        self,
        id: str | None = None,
        *,
        datasetid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        startdate: str = "",  # YYYY-MM-DD
        enddate: str = "",  # YYYY-MM-DD
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.LocationsJSON | json_schemas.RateLimitJSON:
        """
        Query information about locations.

        Args:
            id (str | None, optional): Specific location ID to retrieve. Defaults to None.
            datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
            locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
            stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
            startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
            enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
            sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
            sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
            limit (int, optional): Maximum number of results to return. Defaults to 25.
            offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
            json_schemas.LocationsJSON | json_schemas.RateLimitJSON: Location information or rate limit message.
        """  # noqa: E501
        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/locations"
            if id is None
            else f"{self.ENDPOINT}/locations/{id}",
            parameters={
                "datasetid": "&".join(datasetid)
                if isinstance(datasetid, list)
                else datasetid,
                "locationid": "&".join(locationid)
                if isinstance(locationid, list)
                else locationid,
                "stationid": "&".join(stationid)
                if isinstance(stationid, list)
                else stationid,
                "startdate": startdate,
                "enddate": enddate,
                "sortfield": sortfield,
                "sortorder": sortorder,
                "limit": limit,
                "offset": offset,
            },
        )

        return cast(
            json_schemas.LocationsJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_stations(
        self,
        id: str | None = None,
        *,
        datasetid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        startdate: str = "",  # YYYY-MM-DD
        enddate: str = "",  # YYYY-MM-DD
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.StationsJSON | json_schemas.RateLimitJSON:
        """
        Query information about weather stations.

        Args:
            id (str | None, optional): Specific station ID to retrieve. Defaults to None.
            datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
            locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
            stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
            startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
            enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
            sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
            sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
            limit (int, optional): Maximum number of results to return. Defaults to 25.
            offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
            json_schemas.StationsJSON | json_schemas.RateLimitJSON: Station information or rate limit message.
        """  # noqa: E501

        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/stations"
            if id is None
            else f"{self.ENDPOINT}/stations/{id}",
            parameters={
                "datasetid": "&".join(datasetid)
                if isinstance(datasetid, list)
                else datasetid,
                "locationid": "&".join(locationid)
                if isinstance(locationid, list)
                else locationid,
                "stationid": "&".join(stationid)
                if isinstance(stationid, list)
                else stationid,
                "startdate": startdate,
                "enddate": enddate,
                "sortfield": sortfield,
                "sortorder": sortorder,
                "limit": limit,
                "offset": offset,
            },
        )

        return cast(
            json_schemas.StationsJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_data(
        self,
        datasetid: str,
        startdate: str,  # YYYY-MM-DD
        enddate: str,  # YYYY-MM-DD
        *,
        datatypeid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        units: parameter_schemas.Units = "",
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
        includemetadata: bool = True,
    ) -> json_schemas.DataJSON | json_schemas.RateLimitJSON:
        """
        Query actual climate data based on specified parameters.

        Args:
            datasetid (str): Required. The dataset ID to query.
            startdate (str): Required. Beginning of date range in 'YYYY-MM-DD' format.
            enddate (str): Required. End of date range in 'YYYY-MM-DD' format.
            datatypeid (str | list[str], optional): Filter by data type ID(s). Defaults to "".
            locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
            stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
            units (parameter_schemas.Units, optional): Unit conversion ("standard" or "metric"). Defaults to "".
            sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
            sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
            limit (int, optional): Maximum number of results to return. Defaults to 25.
            offset (int, optional): Number of results to skip for pagination. Defaults to 0.
            includemetadata (bool, optional): Whether to include metadata in the response. Defaults to True.

        Returns:
            json_schemas.DataJSON | json_schemas.RateLimitJSON: Climate data or rate limit message.

        Notes:
            - Annual and monthly data will be limited to a 10-year range.
            - Other data will be limited to a 1-year range.
        """  # noqa: E501

        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/data",
            parameters={
                "datasetid": datasetid,
                "startdate": startdate,
                "enddate": enddate,
                "datatypeid": "&".join(datatypeid)
                if isinstance(datatypeid, list)
                else datatypeid,
                "locationid": "&".join(locationid)
                if isinstance(locationid, list)
                else locationid,
                "stationid": "&".join(stationid)
                if isinstance(stationid, list)
                else stationid,
                "units": units,
                "sortfield": sortfield,
                "sortorder": sortorder,
                "limit": limit,
                "offset": offset,
                "includemetadata": includemetadata,
            },
        )

        return cast(
            json_schemas.DataJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    def close(self):
        """
        Close the aiohttp session.

        This method should be called when the client is no longer needed to properly
        release resources associated with the HTTP session.
        """

        _ = self.aiohttp_session.close()

    def __del__(self):
        """
        Destructor that ensures the aiohttp session is closed when the object is garbage collected.
        """  # noqa: E501
        self.close()

