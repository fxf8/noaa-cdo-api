# pyright: reportExplicitAny=false
# pyright: reportAny=false

import asyncio
import types
import warnings
from collections.abc import Mapping
from enum import Flag, auto
from typing import Any, ClassVar, NamedTuple, Self, cast

import aiohttp
import aiolimiter
from yarl import URL

import noaa_cdo_api.json_schemas as json_schemas
import noaa_cdo_api.parameter_schemas as parameter_schemas


class MissingTokenError(Exception):
    pass


class TokenLocation(Flag):
    NOWHERE = auto()
    IN_CLIENT_SESSION_HEADERS = auto()
    IN_ATTRIBUTE = auto()
    IN_ATTRIBUTES_AND_CLIENT_SESSION_HEADERS = auto()


class Extent(NamedTuple):
    latitude_min: float
    longitude_min: float
    latitude_max: float
    longitude_max: float


class NOAAClient:
    """
    <span style="color:#4E97D8; font-weight:bold">Asynchronous client for accessing the NOAA NCEI Climate Data Online (CDO) Web API v2.</span>

    This client handles API authentication, rate limiting, connection management, and
    provides methods to query all available NOAA CDO endpoints.

    <span style="color:#2ECC71; font-weight:bold">Methods:</span>
    --------
     - <span style="color:#9B59B6">get_datasets</span>: Query information about available datasets.
     - <span style="color:#9B59B6">get_data_categories</span>: Query information about data categories.
     - <span style="color:#9B59B6">get_datatypes</span>: Query information about data types.
     - <span style="color:#9B59B6">get_location_categories</span>: Query information about location categories.
     - <span style="color:#9B59B6">get_locations</span>: Query information about locations.
     - <span style="color:#9B59B6">get_stations</span>: Query information about weather stations.
     - <span style="color:#9B59B6">get_data</span>: Query actual climate data based on specified parameters.
     - <span style="color:#9B59B6">close</span>: Close the aiohttp session.

    <span style="color:#E67E22; font-weight:bold">Important Implementation Notes:</span>
    ------
     - <span style="color:#F1C40F">Event Loop Consistency</span>: Always make requests within the same event loop to
       take advantage of client-side rate limiting and TCP connection pooling. Using different
       event loops will reset rate limiters and require new connection establishment.

     - <span style="color:#F1C40F">Rate Limiting</span>: The client automatically enforces NOAA's API rate limits
       (5 req/sec, 10,000 req/day) through AsyncLimiter. This prevents API throttling or
       blacklisting while optimizing throughput.

     - <span style="color:#F1C40F">Connection Management</span>: Uses aiohttp's TCPConnector for connection pooling and
       reuse, significantly improving performance for multiple requests by avoiding
       the overhead of establishing new connections.

     - <span style="color:#F1C40F">Context Manager Support</span>: The client can be used as an async context manager
       (`async with NOAAClient(...) as client:`) to ensure proper resource cleanup.

    <span style="color:#2ECC71; font-weight:bold">Usage Notes:</span>
    ------
     - All query methods are asynchronous and return parsed JSON responses.
     - For ID-based queries, pass the ID as the first parameter.
     - For broader queries, use the keyword parameters to filter results.
     - Always provide your NOAA API token (sign up at https://www.ncdc.noaa.gov/cdo-web/token)
    """  # noqa: E501

    __slots__: tuple[str, ...] = (
        "token",
        "tcp_connector",
        "aiohttp_session",
        "tcp_connector_limit",
        "keepalive_timeout",
        "is_client_provided",
        "_seconds_request_limiter",
        "_daily_request_limiter",
        "_most_recent_loop",
    )

    token: str | None
    """
    The API token for authentication with NOAA API.
    """

    tcp_connector: aiohttp.TCPConnector | None
    """
    TCP connector for managing HTTP connections. (Lazily initialized)
    """

    aiohttp_session: aiohttp.ClientSession | None
    """
    Aiohttp session for making HTTP requests. (Lazily initialized)
    """

    tcp_connector_limit: int
    """
    Maximum number of connections.
    """

    keepalive_timeout: int
    """
    Timeout for keeping connections alive in seconds.
    """

    is_client_provided: bool
    """
    Flag indicating if the client was provided by the user (using `provide_aiohttp_client_session`). In which case, context management will not close the client.

    NOTE: If the token parameter is not set in the client headers, the `token` parameter will be used. If the `token` parameter is also none, a `MissingTokenError` will be raised.
    """  # noqa: E501

    _seconds_request_limiter: aiolimiter.AsyncLimiter
    """
    Rate limiter for requests per second.
    """

    _daily_request_limiter: aiolimiter.AsyncLimiter
    """
    Rate limiter for requests per day.
    """

    _most_recent_loop: asyncio.AbstractEventLoop | None

    ENDPOINT: ClassVar[URL] = URL("https://www.ncei.noaa.gov/cdo-web/api/v2")
    """
    Base URL for the NOAA CDO API v2.
    """

    def __init__(
        self,
        token: str | None,
        tcp_connector_limit: int = 10,
        keepalive_timeout: int = 60,  # Seconds
    ):
        """
        <span style="color:#4E97D8; font-weight:bold">Initialize the NOAA API client.</span>

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">token</span> (str): The API token for authentication with NOAA API.
           Get a token at: https://www.ncdc.noaa.gov/cdo-web/token
         - <span style="color:#9B59B6">tcp_connector_limit</span> (int, optional): Maximum number of connections.
           Higher limits allow more concurrent requests but consume more resources. Defaults to 10.
         - <span style="color:#9B59B6">keepalive_timeout</span> (int, optional): Timeout for keeping connections alive in seconds.
           Higher values maintain connections longer, reducing overhead for frequent requests. Defaults to 60.

        <span style="color:#2ECC71; font-weight:bold">Notes:</span>
         - Using a higher connector limit is beneficial when making many parallel requests
         - The keepalive timeout should be adjusted based on your request frequency pattern
        """  # noqa: E501
        self.token = token
        self.tcp_connector_limit = tcp_connector_limit
        self.keepalive_timeout = keepalive_timeout
        self.tcp_connector = None
        self.aiohttp_session = None
        self.is_client_provided = False
        self._seconds_request_limiter = aiolimiter.AsyncLimiter(
            5,  # 5 requests per second
            1,  # 1 second
        )

        self._daily_request_limiter = aiolimiter.AsyncLimiter(
            10_000,  # 10_000 requests per day
            60 * 60 * 24,  # 1 day
        )

        self._most_recent_loop = None

    def _find_token_location(self) -> TokenLocation:
        if self.aiohttp_session is None:
            if self.token is None:
                return TokenLocation.NOWHERE
            else:
                return TokenLocation.IN_ATTRIBUTE

        if "token" in self.aiohttp_session.headers and self.token is None:
            return TokenLocation.IN_CLIENT_SESSION_HEADERS

        return TokenLocation.IN_ATTRIBUTES_AND_CLIENT_SESSION_HEADERS

    async def __aenter__(self) -> Self:
        _ = await self._ensure()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: Exception | None,
        traceback: types.TracebackType | None,
    ) -> None:
        if not self.is_client_provided:
            self.close()

    async def provide_aiohttp_client_session(
        self, asyncio_client: aiohttp.ClientSession
    ) -> Self:
        """
        <span style="color:#4E97D8; font-weight:bold">Provide an existing aiohttp session for the client.</span>

        <span style="color:#E67E22; font-weight:bold">Advanced Usage:</span>
        This method allows integrating the NOAA client with an existing aiohttp session,
        useful for applications that need to share connection pools or have complex
        HTTP client requirements.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">asyncio_client</span> (aiohttp.ClientSession): The existing aiohttp session.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - Self: The client instance for method chaining

        <span style="color:#E67E22; font-weight:bold">Important:</span>
        When using a provided session, you are responsible for closing it properly.
        The client will not close it even when using async context management.
        """  # noqa: E501
        self.aiohttp_session = asyncio_client
        self.is_client_provided = True

        return self

    async def _ensure(self) -> TokenLocation:
        """
        <span style="color:#4E97D8; font-weight:bold">Ensures that necessary resources exist for making API requests.</span>

        This method lazily initializes the TCP connector and aiohttp session when needed,
        which allows for efficient resource management and supports integration with
        existing sessions.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - TokenLocation: The location of the token (Enum indicating where the token is stored)

        <span style="color:#E67E22; font-weight:bold">Implementation Notes:</span>
        This method handles the complex logic of determining where the authentication
        token is stored and creating appropriate session headers. It rebuilds connections
        if the event loop has changed, ensuring proper resource management across
        different async contexts.
        """  # noqa: E501
        if self.tcp_connector is not None and self.tcp_connector._loop.is_closed():  # pyright: ignore[reportPrivateUsage]
            self.tcp_connector = None

        if self.aiohttp_session is not None and self.aiohttp_session._loop.is_closed():  # pyright: ignore[reportPrivateUsage]
            self.aiohttp_session = None

        if self.is_client_provided and self.aiohttp_session is None:
            return self._find_token_location()

        if self.tcp_connector is None:
            self.tcp_connector = aiohttp.TCPConnector(
                limit=self.tcp_connector_limit, keepalive_timeout=self.keepalive_timeout
            )

        if self.aiohttp_session is None:
            if self._find_token_location() is TokenLocation.IN_ATTRIBUTE:
                self.aiohttp_session = aiohttp.ClientSession(
                    headers={"token": cast(str, self.token)},
                    connector=self.tcp_connector,
                )

                return TokenLocation.IN_ATTRIBUTES_AND_CLIENT_SESSION_HEADERS

            if self._find_token_location() is TokenLocation.NOWHERE:
                self.aiohttp_session = aiohttp.ClientSession(
                    connector=self.tcp_connector
                )

                return TokenLocation.NOWHERE

        return TokenLocation.IN_CLIENT_SESSION_HEADERS

    async def _make_request(
        self,
        url: URL,
        parameters: parameter_schemas.AnyParameter | None = None,
        token_parameter: str | None = None,
    ) -> Any:
        """
        <span style="color:#4E97D8; font-weight:bold">Internal method to make a rate-limited API request.</span>

        This method is the core mechanism for all API interactions, handling:
        - Event loop tracking and warning if changed
        - Rate limiting (both per-second and daily limits)
        - Token management and authentication
        - Parameter validation
        - HTTP request execution

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">url</span> (str): The API endpoint URL.
         - <span style="color:#9B59B6">parameters</span> (parameter_schemas.AnyParameter | None, optional): Query parameters. Defaults to None.
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence over
           the `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided
           anywhere (client headers or attribute). Token parameter will **not** persist between calls.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - Any: The HTTP response JSON.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If the client header `token`, attribute `token`, and parameter `token_parameter` are all not provided.

        <span style="color:#E67E22; font-weight:bold">Important Implementation Notes:</span>
        - <span style="color:#F1C40F">Event Loop Tracking</span>: Detects when requests are made from different event
          loops and resets rate limiters. For optimal performance, always make requests from
          the same event loop to maintain consistent rate limiting and connection pooling.

        - <span style="color:#F1C40F">Rate Limiting</span>: Uses AsyncLimiter to enforce NOAA's API limits:
          - 5 requests per second
          - 10,000 requests per day
          These limits prevent API throttling while maximizing throughput.

        - <span style="color:#F1C40F">TCP Connection Reuse</span>: Maintains persistent connections to reduce
          latency and overhead. When all requests are made in the same event loop, connections
          are efficiently reused, significantly improving performance.

        - <span style="color:#F1C40F">Token Management</span>: Flexibly handles API tokens from multiple sources,
          with a clear precedence order: token_parameter > session headers > instance attribute.
        """  # noqa: E501
        if self._most_recent_loop is None:
            self._most_recent_loop = asyncio.get_running_loop()

        elif self._most_recent_loop.is_closed():
            warnings.warn(
                "Preivous loop was closed. Please only make requests from the same loop in order to utilize client-side rate limiting and TCP Connection caching",  # noqa: E501
                RuntimeWarning,
                stacklevel=9,
            )

            self._seconds_request_limiter = aiolimiter.AsyncLimiter(
                5,  # 5 requests per second
                1,  # 1 second
            )

            self._daily_request_limiter = aiolimiter.AsyncLimiter(
                10_000,  # 10_000 requests per day
                60 * 60 * 24,  # 1 day
            )

            self._most_recent_loop = asyncio.get_running_loop()

        token_location: TokenLocation = await self._ensure()

        if (
            parameters is not None
            and "limit" in parameters
            and parameters["limit"] > 1000
        ):
            raise ValueError("Parameter 'limit' must be less than or equal to 1000")

        if token_location is TokenLocation.NOWHERE and token_parameter is None:
            raise MissingTokenError(
                "Neither client with token in header nor `token` attribute is provided"
            )

        if token_parameter is not None:
            async with (
                self._seconds_request_limiter,
                self._daily_request_limiter,
                cast(
                    aiohttp.ClientSession, self.aiohttp_session
                ).get(  # Client was already ensured
                    url,
                    params=cast(Mapping[str, str], parameters),
                    headers={"token": token_parameter},
                ) as response,
            ):
                response.raise_for_status()
                return await response.json()

        if (
            token_location is TokenLocation.IN_ATTRIBUTES_AND_CLIENT_SESSION_HEADERS
            or token_location is TokenLocation.IN_CLIENT_SESSION_HEADERS
        ):
            async with (
                self._seconds_request_limiter,
                self._daily_request_limiter,
                cast(
                    aiohttp.ClientSession, self.aiohttp_session
                ).get(  # Client was already ensured
                    url, params=cast(Mapping[str, str | int], parameters)
                ) as response,
            ):
                response.raise_for_status()
                return await response.json()

        if token_location is TokenLocation.IN_ATTRIBUTE:
            async with (
                self._seconds_request_limiter,
                self._daily_request_limiter,
                cast(
                    aiohttp.ClientSession, self.aiohttp_session
                ).get(  # Client was already ensured
                    url,
                    params=cast(Mapping[str, str], parameters),
                    headers={"token": cast(str, self.token)},
                ) as response,
            ):
                response.raise_for_status()
                return await response.json()

    async def get_dataset_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.DatasetIDJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about a specific dataset by ID.</span>
        <span style="color:#3498DB">Endpoint: `/datasets/{id}`</span>

        Retrieves detailed information about a single dataset identified by its unique ID.
        This endpoint provides comprehensive metadata about the dataset's structure, time range,
        coverage, and other attributes.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">id</span> (str): The ID of the dataset to retrieve.
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided
           anywhere (client headers or attribute). Token parameter will **not** persist between calls.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.DatasetIDJSON | json_schemas.RateLimitJSON: Parsed JSON response containing
           dataset information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If the client header `token`, attribute `token`, and parameter `token_parameter` are all not provided.

        <span style="color:#E67E22; font-weight:bold">Performance Note:</span>
        Individual ID lookups are generally faster than filtered queries against all datasets.
        When you know the specific dataset ID, use this method for better performance.
        """  # noqa: E501
        return cast(
            json_schemas.DatasetIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "datasets" / id, token_parameter=token_parameter
            ),
        )

    async def get_datasets(
        self,
        *,
        token_parameter: str | None = None,
        datatypeid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        startdate: str = "0001-01-01",  # YYYY-MM-DD
        enddate: str = "0001-01-01",  # YYYY-MM-DD
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.DatasetsJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about available datasets.</span>
        <span style="color:#3498DB">Endpoint: `/datasets`</span>

        Retrieves a list of datasets matching the specified filter criteria. This endpoint
        allows comprehensive filtering to find datasets containing specific data types,
        locations, date ranges, and more.

        <span style="color:#E67E22; font-weight:bold">Parameter Formatting:</span>
        List parameters are automatically formatted as comma-separated strings.
        Providing a string or list of strings of comma-separated values is also supported.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None.
         - <span style="color:#9B59B6">datatypeid</span> (str | list[str], optional): Filter by data type ID(s). Defaults to "".
         - <span style="color:#9B59B6">locationid</span> (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - <span style="color:#9B59B6">stationid</span> (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - <span style="color:#9B59B6">startdate</span> (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "0001-01-01".
         - <span style="color:#9B59B6">enddate</span> (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "0001-01-01".
         - <span style="color:#9B59B6">sortfield</span> (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - <span style="color:#9B59B6">sortorder</span> (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - <span style="color:#9B59B6">limit</span> (int, optional): Maximum number of results to return. Defaults to 25.
         - <span style="color:#9B59B6">offset</span> (int, optional): Number of results to skip for pagination. Defaults to 0.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.DatasetsJSON | json_schemas.RateLimitJSON: Dataset information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If authentication is missing.

        <span style="color:#E67E22; font-weight:bold">Performance Tips:</span>
        - Use as many filter parameters as possible to reduce result size and improve response time
        - For large result sets, use pagination (limit and offset) to retrieve data in manageable chunks
        - Consider caching results for frequently accessed dataset information
        """  # noqa: E501
        return cast(
            json_schemas.DatasetsJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "datasets",
                parameters={
                    "datatypeid": ",".join(datatypeid)
                    if isinstance(datatypeid, list)
                    else datatypeid,
                    "locationid": ",".join(locationid)
                    if isinstance(locationid, list)
                    else locationid,
                    "stationid": ",".join(stationid)
                    if isinstance(stationid, list)
                    else stationid,
                    "startdate": startdate,
                    "enddate": enddate,
                    "sortfield": sortfield,
                    "sortorder": sortorder,
                    "limit": limit,
                    "offset": offset,
                },
                token_parameter=token_parameter,
            ),
        )

    async def get_data_category_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.DatacategoryIDJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about a specific data category by ID.</span>
        <span style="color:#3498DB">Endpoint: `/datacategories/{id}`</span>

        Retrieves detailed information about a single data category identified by its unique ID.
        Data categories represent broad classifications of the types of data available.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">id</span> (str): The ID of the data category to retrieve.
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided
           anywhere (client headers or attribute). Token parameter will **not** persist between calls.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.DatacategoryIDJSON | json_schemas.RateLimitJSON: Parsed JSON response containing
           data category information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If the client header `token`, attribute `token`, and parameter `token_parameter` are all not provided.

        <span style="color:#E67E22; font-weight:bold">Note:</span>
        Individual ID lookups are more efficient than querying all data categories when you know the specific ID.
        """  # noqa: E501
        return cast(
            json_schemas.DatacategoryIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "datacategories" / id, token_parameter=token_parameter
            ),
        )

    async def get_data_categories(
        self,
        *,
        token_parameter: str | None = None,
        datasetid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        startdate: str = "0001-01-01",
        enddate: str = "9999-01-01",
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about available data categories.</span>
        <span style="color:#3498DB">Endpoint: `/datacategories`</span>

        Retrieves a list of data categories matching the specified filter criteria. Data categories
        are high-level classifications for the types of data available through the NOAA API.

        <span style="color:#E67E22; font-weight:bold">Parameter Formatting:</span>
        List parameters are automatically formatted as comma-separated strings.
        Providing a string or list of strings of comma-separated values is also supported.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None.
         - <span style="color:#9B59B6">datasetid</span> (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - <span style="color:#9B59B6">locationid</span> (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - <span style="color:#9B59B6">stationid</span> (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - <span style="color:#9B59B6">startdate</span> (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "0001-01-01".
         - <span style="color:#9B59B6">enddate</span> (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "9999-01-01".
         - <span style="color:#9B59B6">sortfield</span> (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - <span style="color:#9B59B6">sortorder</span> (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - <span style="color:#9B59B6">limit</span> (int, optional): Maximum number of results to return. Defaults to 25.
         - <span style="color:#9B59B6">offset</span> (int, optional): Number of results to skip for pagination. Defaults to 0.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON: Data categories information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If authentication is missing.

        <span style="color:#E67E22; font-weight:bold">Usage Tip:</span>
        Data categories are useful for exploratory navigation of the NOAA data. Use this endpoint to
        discover broad categories before drilling down to specific data types within those categories.
        """  # noqa: E501
        return cast(
            json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "datacategories",
                parameters={
                    "datasetid": ",".join(datasetid)
                    if isinstance(datasetid, list)
                    else datasetid,
                    "locationid": ",".join(locationid)
                    if isinstance(locationid, list)
                    else locationid,
                    "stationid": ",".join(stationid)
                    if isinstance(stationid, list)
                    else stationid,
                    "startdate": startdate,
                    "enddate": enddate,
                    "sortfield": sortfield,
                    "sortorder": sortorder,
                    "limit": limit,
                    "offset": offset,
                },
                token_parameter=token_parameter,
            ),
        )

    async def get_datatype_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.DatatypeIDJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about a specific data type by ID.</span>
        <span style="color:#3498DB">Endpoint: `/datatypes/{id}`</span>

        Retrieves detailed information about a single data type identified by its unique ID.
        Data types represent specific measurements or observations available in the NOAA datasets.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">id</span> (str): The ID of the data type to retrieve.
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided
           anywhere (client headers or attribute). Token parameter will **not** persist between calls.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.DatatypeIDJSON | json_schemas.RateLimitJSON: Parsed JSON response containing
           data type information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If the client header `token`, attribute `token`, and parameter `token_parameter` are all not provided.

        <span style="color:#E67E22; font-weight:bold">Data Type Details:</span>
        Individual data type records include information about the measurement units, period,
        and other important metadata that helps interpret the actual climate data.
        """  # noqa: E501
        return cast(
            json_schemas.DatatypeIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "datatypes/" / id, token_parameter=token_parameter
            ),
        )

    async def get_datatypes(
        self,
        *,
        token_parameter: str | None = None,
        datasetid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        datacategoryid: str | list[str] = "",
        startdate: str = "0001-01-01",
        enddate: str = "9999-01-01",
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.DatatypesJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about available data types.</span>
        <span style="color:#3498DB">Endpoint: `/datatypes`</span>

        Retrieves a list of data types matching the specified filter criteria. Data types
        represent specific climate measurements or observations available in the NOAA datasets,
        such as temperature, precipitation, wind speed, etc.

        <span style="color:#E67E22; font-weight:bold">Parameter Formatting:</span>
        List parameters are automatically formatted as comma-separated strings.
        Providing a string or list of strings of comma-separated values is also supported.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None.
         - <span style="color:#9B59B6">datasetid</span> (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - <span style="color:#9B59B6">locationid</span> (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - <span style="color:#9B59B6">stationid</span> (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - <span style="color:#9B59B6">datacategoryid</span> (str | list[str], optional): Filter by data category ID(s). Defaults to "".
         - <span style="color:#9B59B6">startdate</span> (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "0001-01-01".
         - <span style="color:#9B59B6">enddate</span> (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "9999-01-01".
         - <span style="color:#9B59B6">sortfield</span> (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - <span style="color:#9B59B6">sortorder</span> (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - <span style="color:#9B59B6">limit</span> (int, optional): Maximum number of results to return. Defaults to 25.
         - <span style="color:#9B59B6">offset</span> (int, optional): Number of results to skip for pagination. Defaults to 0.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.DatatypesJSON | json_schemas.RateLimitJSON: Data types information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If authentication is missing.

        <span style="color:#E67E22; font-weight:bold">Research Tip:</span>
        When planning a climate data analysis project, first explore available data types to
        determine which measurements are available for your region and time period of interest.
        Use datacategoryid to narrow down to relevant measurement categories.
        """  # noqa: E501
        return cast(
            json_schemas.DatatypesJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "datatypes",
                parameters={
                    "datasetid": ",".join(datasetid)
                    if isinstance(datasetid, list)
                    else datasetid,
                    "locationid": ",".join(locationid)
                    if isinstance(locationid, list)
                    else locationid,
                    "stationid": ",".join(stationid)
                    if isinstance(stationid, list)
                    else stationid,
                    "datacategoryid": ",".join(datacategoryid)
                    if isinstance(datacategoryid, list)
                    else datacategoryid,
                    "startdate": startdate,
                    "enddate": enddate,
                    "sortfield": sortfield,
                    "sortorder": sortorder,
                    "limit": limit,
                    "offset": offset,
                },
                token_parameter=token_parameter,
            ),
        )

    async def get_location_category_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.LocationcategoryIDJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about a specific location category by ID.</span>
        <span style="color:#3498DB">Endpoint: `/locationcategories/{id}`</span>

        Retrieves detailed information about a single location category identified by its unique ID.
        Location categories classify the types of locations available in the NOAA data (e.g., cities, counties, states).

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">id</span> (str): The ID of the location category to retrieve.
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided
           anywhere (client headers or attribute). Token parameter will **not** persist between calls.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.LocationcategoryIDJSON | json_schemas.RateLimitJSON: Parsed JSON response containing
           location category information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If the client header `token`, attribute `token`, and parameter `token_parameter` are all not provided.

        <span style="color:#E67E22; font-weight:bold">Usage Context:</span>
        Location categories provide a way to understand the different geographical hierarchies
        available in the NOAA climate data. This is particularly useful when designing
        geospatial visualizations or analyses across different territorial divisions.
        """  # noqa: E501
        return cast(
            json_schemas.LocationcategoryIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "locationcategories" / id,
                token_parameter=token_parameter,
            ),
        )

    async def get_location_categories(
        self,
        *,
        token_parameter: str | None = None,
        datasetid: str | list[str] = "",
        locationid: str | list[str] = "",
        startdate: str = "0001-01-01",
        enddate: str = "9999-01-01",
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about available location categories.</span>
        <span style="color:#3498DB">Endpoint: `/locationcategories`</span>

        Retrieves a list of location categories matching the specified filter criteria. Location categories
        classify the geographical hierarchies available in the NOAA climate data, such as cities, counties,
        states, countries, or other territorial divisions.

        <span style="color:#E67E22; font-weight:bold">Parameter Formatting:</span>
        List parameters are automatically formatted as comma-separated strings.
        Providing a string or list of strings of comma-separated values is also supported.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None.
         - <span style="color:#9B59B6">datasetid</span> (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - <span style="color:#9B59B6">locationid</span> (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - <span style="color:#9B59B6">startdate</span> (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "0001-01-01".
         - <span style="color:#9B59B6">enddate</span> (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "9999-01-01".
         - <span style="color:#9B59B6">sortfield</span> (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - <span style="color:#9B59B6">sortorder</span> (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - <span style="color:#9B59B6">limit</span> (int, optional): Maximum number of results to return. Defaults to 25.
         - <span style="color:#9B59B6">offset</span> (int, optional): Number of results to skip for pagination. Defaults to 0.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON: Location categories information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If authentication is missing.

        <span style="color:#E67E22; font-weight:bold">Geographical Analysis Tip:</span>
        Location categories help organize spatial data into logical hierarchies. When designing
        geographical analyses, first explore the available location categories to determine
        the most appropriate spatial resolution for your research question.
        """  # noqa: E501
        return cast(
            json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "locationcategories",
                parameters={
                    "datasetid": ",".join(datasetid)
                    if isinstance(datasetid, list)
                    else datasetid,
                    "locationid": ",".join(locationid)
                    if isinstance(locationid, list)
                    else locationid,
                    "startdate": startdate,
                    "enddate": enddate,
                    "sortfield": sortfield,
                    "sortorder": sortorder,
                    "limit": limit,
                    "offset": offset,
                },
                token_parameter=token_parameter,
            ),
        )

    async def get_location_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.LocationIDJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about a specific location by ID.</span>
        <span style="color:#3498DB">Endpoint: `/locations/{id}`</span>

        Retrieves detailed information about a single location identified by its unique ID.
        Locations represent geographical areas where climate data is collected.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">id</span> (str): The ID of the location to retrieve.
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided
           anywhere (client headers or attribute). Token parameter will **not** persist between calls.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.LocationIDJSON | json_schemas.RateLimitJSON: Parsed JSON response containing
           location information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If the client header `token`, attribute `token`, and parameter `token_parameter` are all not provided.

        <span style="color:#E67E22; font-weight:bold">Location Details:</span>
        Individual location records include important metadata such as coordinates, names,
        and other geographical attributes that help interpret the climate data associated
        with the location.
        """  # noqa: E501
        return cast(
            json_schemas.LocationIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "locations" / id, token_parameter=token_parameter
            ),
        )

    async def get_locations(
        self,
        *,
        token_parameter: str | None = None,
        datasetid: str | list[str] = "",
        locationcategoryid: str | list[str] = "",
        datacategoryid: str | list[str] = "",
        startdate: str = "0001-01-01",
        enddate: str = "9999-01-01",
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.LocationsJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about available locations.</span>
        <span style="color:#3498DB">Endpoint: `/locations`</span>

        Retrieves a list of locations matching the specified filter criteria. Locations represent
        geographical areas where climate data is collected, such as cities, counties, states,
        countries, or other territorial divisions.

        <span style="color:#E67E22; font-weight:bold">Parameter Formatting:</span>
        List parameters are automatically formatted as comma-separated strings.
        Providing a string or list of strings of comma-separated values is also supported.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None.
         - <span style="color:#9B59B6">datasetid</span> (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - <span style="color:#9B59B6">locationcategoryid</span> (str | list[str], optional): Filter by location category ID(s). Defaults to "".
         - <span style="color:#9B59B6">datacategoryid</span> (str | list[str], optional): Filter by data category ID(s). Defaults to "".
         - <span style="color:#9B59B6">startdate</span> (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "0001-01-01".
         - <span style="color:#9B59B6">enddate</span> (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "9999-01-01".
         - <span style="color:#9B59B6">sortfield</span> (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - <span style="color:#9B59B6">sortorder</span> (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - <span style="color:#9B59B6">limit</span> (int, optional): Maximum number of results to return. Defaults to 25.
         - <span style="color:#9B59B6">offset</span> (int, optional): Number of results to skip for pagination. Defaults to 0.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.LocationsJSON | json_schemas.RateLimitJSON: Locations information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If authentication is missing.

        <span style="color:#E67E22; font-weight:bold">Spatial Analysis Tip:</span>
        When working with climate data across geographical regions, use the locationcategoryid
        parameter to narrow down locations to a specific category (e.g., states, countries)
        for more consistent analysis. Combine with datacategoryid to find locations where
        specific types of measurements are available.
        """  # noqa: E501
        return cast(
            json_schemas.LocationsJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "locations",
                parameters={
                    "datasetid": ",".join(datasetid)
                    if isinstance(datasetid, list)
                    else datasetid,
                    "locationcategoryid": ",".join(locationcategoryid)
                    if isinstance(locationcategoryid, list)
                    else locationcategoryid,
                    "datacategoryid": ",".join(datacategoryid)
                    if isinstance(datacategoryid, list)
                    else datacategoryid,
                    "startdate": startdate,
                    "enddate": enddate,
                    "sortfield": sortfield,
                    "sortorder": sortorder,
                    "limit": limit,
                    "offset": offset,
                },
                token_parameter=token_parameter,
            ),
        )

    async def get_station_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.StationIDJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about a specific weather station by ID.</span>
        <span style="color:#3498DB">Endpoint: `/stations/{id}`</span>

        Retrieves detailed information about a single weather station identified by its unique ID.
        Stations are physical locations where weather and climate data measurements are collected.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">id</span> (str): The ID of the station to retrieve.
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided
           anywhere (client headers or attribute). Token parameter will **not** persist between calls.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.StationIDJSON | json_schemas.RateLimitJSON: Parsed JSON response containing
           station information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If the client header `token`, attribute `token`, and parameter `token_parameter` are all not provided.

        <span style="color:#E67E22; font-weight:bold">Data Precision:</span>
        Weather stations provide the most accurate and localized climate data since they
        represent exact measurement points. Station-level data is particularly valuable
        for precise local analyses and ground-truthing other data sources.
        """  # noqa: E501
        return cast(
            json_schemas.StationIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "stations" / id, token_parameter=token_parameter
            ),
        )

    async def get_stations(
        self,
        *,
        token_parameter: str | None = None,
        datasetid: str | list[str] = "",
        locationid: str | list[str] = "",
        datacategoryid: str | list[str] = "",
        datatypeid: str | list[str] = "",
        extent: Extent | str = "",
        startdate: str = "0001-01-01",
        enddate: str = "9999-01-01",
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
    ) -> json_schemas.StationsJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query information about available weather stations.</span>
        <span style="color:#3498DB">Endpoint: `/stations`</span>

        Retrieves a list of weather stations matching the specified filter criteria. Weather stations
        are the physical locations where climate measurements are recorded, and typically provide
        the most precise and localized data available.

        <span style="color:#E67E22; font-weight:bold">Parameter Formatting:</span>
        List parameters are automatically formatted as comma-separated strings.
        Providing a string or list of strings of comma-separated values is also supported.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None.
         - <span style="color:#9B59B6">datasetid</span> (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - <span style="color:#9B59B6">locationid</span> (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - <span style="color:#9B59B6">datacategoryid</span> (str | list[str], optional): Filter by data category ID(s). Defaults to "".
         - <span style="color:#9B59B6">datatypeid</span> (str | list[str], optional): Filter by data type ID(s). Defaults to "".
         - <span style="color:#9B59B6">extent</span> (Extent | str, optional): Geospatial extent (bbox) filter in format "latitude_min,longitude_min,latitude_max,longitude_max" if string or `noaa.Extent`. Defaults to "".
         - <span style="color:#9B59B6">startdate</span> (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "0001-01-01".
         - <span style="color:#9B59B6">enddate</span> (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "9999-01-01".
         - <span style="color:#9B59B6">sortfield</span> (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - <span style="color:#9B59B6">sortorder</span> (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - <span style="color:#9B59B6">limit</span> (int, optional): Maximum number of results to return. Defaults to 25.
         - <span style="color:#9B59B6">offset</span> (int, optional): Number of results to skip for pagination. Defaults to 0.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.StationsJSON | json_schemas.RateLimitJSON: Stations information or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If authentication is missing.

        <span style="color:#E67E22; font-weight:bold">Geospatial Filtering:</span>
        The stations endpoint is one of the few that supports the "extent" parameter for
        geographical bounding box filtering. This is particularly useful for finding all
        stations within a specific region defined by coordinates. For example:
        "extent=42.0,-90.0,40.0,-88.0" would find stations within that rectangle.
        """  # noqa: E501

        return cast(
            json_schemas.StationsJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "stations",
                parameters={
                    "datasetid": ",".join(datasetid)
                    if isinstance(datasetid, list)
                    else datasetid,
                    "locationid": ",".join(locationid)
                    if isinstance(locationid, list)
                    else locationid,
                    "datacategoryid": ",".join(datacategoryid)
                    if isinstance(datacategoryid, list)
                    else datacategoryid,
                    "datatypeid": ",".join(datatypeid)
                    if isinstance(datatypeid, list)
                    else datatypeid,
                    "extent": f"{extent.latitude_min},{extent.longitude_min},{extent.latitude_max},{extent.longitude_max}"  # noqa: E501
                    if isinstance(extent, Extent)
                    else extent,
                    "startdate": startdate,
                    "enddate": enddate,
                    "sortfield": sortfield,
                    "sortorder": sortorder,
                    "limit": limit,
                    "offset": offset,
                },
                token_parameter=token_parameter,
            ),
        )

    async def get_data(
        self,
        datasetid: str,
        startdate: str,  # YYYY-MM-DD
        enddate: str,  # YYYY-MM-DD
        *,
        token_parameter: str | None = None,
        datatypeid: str | list[str] = "",
        locationid: str | list[str] = "",
        stationid: str | list[str] = "",
        units: parameter_schemas.Units = "",
        sortfield: parameter_schemas.DataSortField = "date",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
        includemetadata: bool = True,
    ) -> json_schemas.DataJSON | json_schemas.RateLimitJSON:
        """
        <span style="color:#4E97D8; font-weight:bold">Query actual climate data with various filtering options.</span>
        <span style="color:#3498DB">Endpoint: `/data`</span>

        This is the primary endpoint for retrieving actual climate measurements and observations.
        Unlike the other endpoints which provide metadata, this endpoint returns the actual
        climate data values matching your specified criteria.

        <span style="color:#E67E22; font-weight:bold">Required Parameters:</span>
        Note that datasetid, startdate, and enddate are all required parameters for this endpoint.
        This is different from other endpoints where all filter parameters are optional.

        <span style="color:#E67E22; font-weight:bold">Parameter Formatting:</span>
        List parameters are automatically formatted as comma-separated strings.
        Providing a string or list of strings of comma-separated values is also supported.

        <span style="color:#2ECC71; font-weight:bold">Args:</span>
         - <span style="color:#9B59B6">token_parameter</span> (str | None, optional): Token parameter which takes precedence
           over `token` attribute. Defaults to None.
         - <span style="color:#9B59B6">datasetid</span> (str): **Required**. The dataset ID to query data from.
         - <span style="color:#9B59B6">startdate</span> (str): **Required**. Beginning of date range in 'YYYY-MM-DD' format.
         - <span style="color:#9B59B6">enddate</span> (str): **Required**. End of date range in 'YYYY-MM-DD' format.
         - <span style="color:#9B59B6">datatypeid</span> (str | list[str], optional): Filter by data type ID(s). Defaults to "".
         - <span style="color:#9B59B6">locationid</span> (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - <span style="color:#9B59B6">stationid</span> (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - <span style="color:#9B59B6">units</span> (parameter_schemas.Units, optional): Unit system for data values ("standard", "metric", or ""). Defaults to "".
         - <span style="color:#9B59B6">sortfield</span> (parameter_schemas.DataSortfield, optional): Field to sort results by. Defaults to "date".
         - <span style="color:#9B59B6">sortorder</span> (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - <span style="color:#9B59B6">limit</span> (int, optional): Maximum number of results to return. Defaults to 25.
         - <span style="color:#9B59B6">offset</span> (int, optional): Number of results to skip for pagination. Defaults to 0.
         - <span style="color:#9B59B6">includemetadata</span> (bool, optional): Whether to include metadata in the response. Defaults to True.

        <span style="color:#2ECC71; font-weight:bold">Returns:</span>
         - json_schemas.DataJSON | json_schemas.RateLimitJSON: Climate data or rate limit message.

        <span style="color:#E74C3C; font-weight:bold">Raises:</span>
         - ValueError: If 'limit' parameter exceeds 1000 or if required parameters are missing.
         - aiohttp.ClientResponseError: If the request fails.
         - MissingTokenError: If authentication is missing.

        <span style="color:#E67E22; font-weight:bold">Data Volume Considerations:</span>
        Climate data queries can return large volumes of data, especially with broad date ranges
        or multiple stations/locations. To manage data volume:

        1. Use narrow date ranges when possible
        2. Specify particular stations or locations instead of querying all
        3. Filter to only the data types you need
        4. Use pagination (limit and offset) for large result sets
        5. Consider setting includemetadata=False if you don't need the metadata

        <span style="color:#E67E22; font-weight:bold">Performance Note:</span>
        This endpoint is often the most resource-intensive and may take longer to respond
        than metadata endpoints. When developing applications, implement appropriate timeout
        handling and consider caching frequently accessed data.
        """  # noqa: E501

        return cast(
            json_schemas.DataJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                self.ENDPOINT / "data",
                parameters={
                    "datasetid": datasetid,
                    "startdate": startdate,
                    "enddate": enddate,
                    "datatypeid": ",".join(datatypeid)
                    if isinstance(datatypeid, list)
                    else datatypeid,
                    "locationid": ",".join(locationid)
                    if isinstance(locationid, list)
                    else locationid,
                    "stationid": ",".join(stationid)
                    if isinstance(stationid, list)
                    else stationid,
                    "units": units,
                    "sortfield": sortfield,
                    "sortorder": sortorder,
                    "limit": limit,
                    "offset": offset,
                    "includemetadata": "true" if includemetadata else "false",
                },
                token_parameter=token_parameter,
            ),
        )

    def close(self) -> None:
        """
        <span style="color:#4E97D8; font-weight:bold">Close the aiohttp session and TCP connector.</span>

        This method properly cleans up resources used by the client. It should be called
        when you're done using the client to ensure proper cleanup of network connections
        and resources.

        <span style="color:#E67E22; font-weight:bold">Resource Management:</span>
        - Always call this method when you're finished with the client
        - Alternatively, use the client as an async context manager with the `async with` statement,
          which will automatically close resources on exit
        - If you provided your own aiohttp session with `provide_aiohttp_client_session()`,
          this method will not close that session

        <span style="color:#E67E22; font-weight:bold">Implementation Note:</span>
        This is a synchronous method that doesn't properly close the aiohttp session, which
        should be closed using `await session.close()`. For proper async cleanup, use
        the client as an async context manager instead.
        """  # noqa: E501

        if isinstance(self.aiohttp_session, aiohttp.ClientSession):
            try:
                loop = asyncio.get_event_loop()
                _ = loop.create_task(self.aiohttp_session.close())

            except RuntimeError:
                asyncio.run(self.aiohttp_session.close())

    def __del__(self):
        """
        Destructor that ensures the aiohttp session is closed when the object is garbage collected.
        """  # noqa: E501
        self.close()
