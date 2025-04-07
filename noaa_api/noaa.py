# pyright: reportExplicitAny=false
# pyright: reportAny=false

import asyncio
from collections.abc import Mapping
from enum import Enum
from typing import Any, ClassVar, Self, cast

import aiohttp
import aiolimiter

import noaa_api.json_schemas as json_schemas
import noaa_api.parameter_schemas as parameter_schemas


class MissingTokenError(Exception):
    pass


class TokenLocation(Enum):
    Nowhere = 0
    InClientSessionHeaders = 1
    InAttribute = 2
    InAttributesAndClientSessionHeaders = 3


class NOAAClient:
    """
    Asynchronous client for accessing the NOAA NCEI Climate Data Online (CDO) Web API v2.

    This client handles API authentication, rate limiting, connection management, and
    provides methods to query all available NOAA CDO endpoints.

    Methods:
    --------
     - get_datasets: Query information about available datasets.
     - get_data_categories: Query information about data categories.
     - get_datatypes: Query information about data types.
     - get_location_categories: Query information about location categories.
     - get_locations: Query information about locations.
     - get_stations: Query information about weather stations.
     - get_data: Query actual climate data based on specified parameters.
     - close: Close the aiohttp session.

    Notes:
    ------
     - All query methods are asynchronous and return parsed JSON responses.
     - The client automatically enforces NOAA's API rate limits (5 req/sec, 10,000 req/day).
     - For ID-based queries, pass the ID as the first parameter.
     - For broader queries, use the keyword parameters to filter results.
    """  # noqa: E501

    __slots__: tuple[str, ...] = (
        "token",
        "tcp_connector",
        "aiohttp_session",
        "tcp_connector_limit",
        "keepalive_timeout",
        "is_client_provided",
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

    ENDPOINT: ClassVar[str] = "https://www.ncei.noaa.gov/cdo-web/api/v2"
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
        Initialize the NOAA API client.

        Args:
         - token (str): The API token for authentication with NOAA API.
         - tcp_connector_limit (int, optional): Maximum number of connections. Defaults to 10.
         - keepalive_timeout (int, optional): Timeout for keeping connections alive in seconds. Defaults to 60.
        """  # noqa: E501

        self.token = token
        self.tcp_connector_limit = tcp_connector_limit
        self.keepalive_timeout = keepalive_timeout
        self.tcp_connector = None
        self.aiohttp_session = None
        self.is_client_provided = False

    def _find_token_location(self) -> TokenLocation:
        if self.aiohttp_session is None:
            if self.token is None:
                return TokenLocation.Nowhere
            else:
                return TokenLocation.InAttribute

        if "token" in self.aiohttp_session.headers and self.token is None:
            return TokenLocation.InClientSessionHeaders

        return TokenLocation.InAttributesAndClientSessionHeaders

    async def provide_aiohttp_client_session(
        self, asyncio_client: aiohttp.ClientSession
    ) -> Self:
        """
        Provide an existing aiohttp session for the client.

        Args:
         - asyncio_client (aiohttp.ClientSession): The existing aiohttp session.

        Returns:
         - None
        """

        self.aiohttp_session = asyncio_client
        self.is_client_provided = True

        return self

    async def _ensure(self) -> TokenLocation:
        """
        Ensures that there exists necessary resources for making api requests.

        Returns:
         - TokenLocation: The location of the token.
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
            if self._find_token_location() == TokenLocation.InAttribute:
                self.aiohttp_session = aiohttp.ClientSession(
                    headers={"token": cast(str, self.token)},
                    connector=self.tcp_connector,
                )

                return TokenLocation.InAttributesAndClientSessionHeaders

            if self._find_token_location() == TokenLocation.Nowhere:
                self.aiohttp_session = aiohttp.ClientSession(
                    connector=self.tcp_connector
                )

                return TokenLocation.Nowhere

        return TokenLocation.InClientSessionHeaders

    async def _make_request(
        self,
        url: str,
        parameters: parameter_schemas.AnyParameter | None = None,
        token_parameter: str | None = None,
    ) -> Any:
        """
        Internal method to make a rate-limited API request.

        Args:
         - url (str): The API endpoint URL.
         - parameters (parameter_schemas.AnyParameter | None, optional): Query parameters. Defaults to None.
         - token_parameter (str | None, optional): Token parameter which take precedence over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided anywhere (client headers or attribute). Token parameter will **not** persist between calls.

        Returns:
         - Any: The HTTP response json.

        Raises:
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        token_location: TokenLocation = await self._ensure()

        if (
            parameters is not None
            and "limit" in parameters
            and parameters["limit"] > 1000
        ):
            raise ValueError("Parameter 'limit' must be less than or equal to 1000")

        if token_location == TokenLocation.Nowhere and token_parameter is None:
            raise MissingTokenError(
                "Neither client with token in header nor `token` attribute is provided"
            )

        seconds_request_limiter = aiolimiter.AsyncLimiter(
            5,  # 5 requests per second
            1,  # 1 second
        )

        daily_request_limiter = aiolimiter.AsyncLimiter(
            10_000,  # 10_000 requests per day
            60 * 60 * 24,  # 1 day
        )

        if token_parameter is not None:
            async with (
                seconds_request_limiter,
                daily_request_limiter,
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
            token_location == TokenLocation.InAttributesAndClientSessionHeaders
            or TokenLocation.InClientSessionHeaders
        ):
            async with (
                seconds_request_limiter,
                daily_request_limiter,
                cast(
                    aiohttp.ClientSession, self.aiohttp_session
                ).get(  # Client was already ensured
                    url, params=cast(Mapping[str, str], parameters)
                ) as response,
            ):
                response.raise_for_status()
                return await response.json()

        if token_location == TokenLocation.InAttribute:
            async with (
                seconds_request_limiter,
                daily_request_limiter,
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
        Query information about a specific dataset by ID.

        Args:
         - id (str): The ID of the dataset to retrieve.
         - token_parameter (str | None, optional): Token parameter which take precedence over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided anywhere (client headers or attribute). Token parameter will **not** persist between calls.


        Returns:
         - json_schemas.DatasetIDJSON: Parsed JSON response containing dataset information.

        Raises:
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.DatasetIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/datasets/{id}", token_parameter=token_parameter
            ),
        )

    async def get_datasets(
        self,
        *,
        token_parameter: str | None = None,
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

        Note: List parameters are automatically formatted as ampersand separated strings. Porviding a string or list of strings of amersand separaated values is also supported.

        Args:
         - token_parameter (str | None, optional): Token parameter which take precedence over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided anywhere (client headers or attribute). Token parameter will **not** persist between calls.
         - datatypeid (str | list[str], optional): Filter by data type ID(s). Defaults to "".
         - locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
         - enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
         - sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - limit (int, optional): Maximum number of results to return. Defaults to 25.
         - offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
         - json_schemas.DatasetsJSON | json_schemas.RateLimitJSON: Dataset information or rate limit message.

        Raises:
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.DatasetsJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/datasets",
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
                token_parameter=token_parameter,
            ),
        )

    async def get_data_category_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.DatacategoryIDJSON | json_schemas.RateLimitJSON:
        """
        Query information about a specific data category by ID.

        Args:
         - id (str): The ID of the data category to retrieve.
         - token_parameter (str | None, optional): Token parameter which take precedence over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided anywhere (client headers or attribute). Token parameter will **not** persist between calls.

        Returns:
         - json_schemas.DatacategoryIDJSON: Parsed JSON response containing data category information.

        Raises:
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.DatacategoryIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/datacategories/{id}", token_parameter=token_parameter
            ),
        )

    async def get_data_categories(
        self,
        *,
        token_parameter: str | None = None,
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
        Query information about data categories. Porviding a string or list of strings of amersand separaated values is also supported.


        Args:
         - token_parameter (str | None, optional): Token parameter which take precedence over `token` attribute. Defaults to None. Can be provided if `token` attribute is not provided anywhere (client headers or attribute). Token parameter will **not** persist between calls.
         - datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
         - enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
         - sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - limit (int, optional): Maximum number of results to return. Defaults to 25.
         - offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
         - json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON: Data category information or rate limit message.


        Raises:
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/datacategories",
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
                token_parameter=token_parameter,
            ),
        )

    async def get_datatype_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.DatatypeIDJSON | json_schemas.RateLimitJSON:
        """
        Query information about a specific data type by ID.

        Args:
         - id (str): The ID of the data type to retrieve.

        Returns:
         - json_schemas.DatatypeIDJSON: Parsed JSON response containing data type information.

        Raises:
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.DatatypeIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/datatypes/{id}", token_parameter=token_parameter
            ),
        )

    async def get_datatypes(
        self,
        *,
        token_parameter: str | None = None,
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
        Query information about data types. Porviding a string or list of strings of amersand separaated values is also supported.


        Args:
         - datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
         - enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
         - sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - limit (int, optional): Maximum number of results to return. Defaults to 25.
         - offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
         - json_schemas.DatatypesJSON | json_schemas.RateLimitJSON: Data type information or rate limit message.

        Raises:
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.DatatypesJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/datatypes",
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
                token_parameter=token_parameter,
            ),
        )

    async def get_locationcategory_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.LocationcategoryIDJSON | json_schemas.RateLimitJSON:
        """
        Query information about a specific location category by ID.

        Args:
         - id (str): The ID of the location category to retrieve.

        Returns:
         - json_schemas.LocationcategoryIDJSON: Parsed JSON response containing location category information.

        Raises:
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.LocationcategoryIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/locationcategories/{id}",
                token_parameter=token_parameter,
            ),
        )

    async def get_location_categories(
        self,
        *,
        token_parameter: str | None = None,
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
        Query information about location categories. Porviding a string or list of strings of amersand separaated values is also supported.


        Args:
         - datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
         - enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
         - sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - limit (int, optional): Maximum number of results to return. Defaults to 25.
         - offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
         - json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON: Location category information or rate limit message.

        Raises:
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501
        return cast(
            json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/locationcategories",
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
                token_parameter=token_parameter,
            ),
        )

    async def get_location_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.LocationIDJSON | json_schemas.RateLimitJSON:
        """
        Query information about a specific location by ID.

        Args:
         - id (str): The ID of the location to retrieve.

        Returns:
         - json_schemas.LocationIDJSON: Parsed JSON response containing location information.

        Raises:
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.LocationIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/locations/{id}", token_parameter=token_parameter
            ),
        )

    async def get_locations(
        self,
        *,
        token_parameter: str | None = None,
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
        Query information about locations. Porviding a string or list of strings of amersand separaated values is also supported.


        Args:
         - datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
         - enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
         - sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - limit (int, optional): Maximum number of results to return. Defaults to 25.
         - offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
         - json_schemas.LocationsJSON | json_schemas.RateLimitJSON: Location information or rate limit message.

        Raises:
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501
        return cast(
            json_schemas.LocationsJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/locations",
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
                token_parameter=token_parameter,
            ),
        )

    async def get_stations_by_id(
        self, id: str, token_parameter: str | None = None
    ) -> json_schemas.StationIDJSON | json_schemas.RateLimitJSON:
        """
        Query information about a specific station by ID.

        Args:
         - id (str): The ID of the station to retrieve.

        Returns:
         - json_schemas.StationsIDJSON: Parsed JSON response containing station information.

        Raises:
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.StationIDJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/stations/{id}", token_parameter=token_parameter
            ),
        )

    async def get_stations(
        self,
        *,
        token_parameter: str | None = None,
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
        Query information about weather stations. Porviding a string or list of strings of amersand separaated values is also supported.


        Args:
         - datasetid (str | list[str], optional): Filter by dataset ID(s). Defaults to "".
         - locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - startdate (str, optional): Beginning of date range in 'YYYY-MM-DD' format. Defaults to "".
         - enddate (str, optional): End of date range in 'YYYY-MM-DD' format. Defaults to "".
         - sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - limit (int, optional): Maximum number of results to return. Defaults to 25.
         - offset (int, optional): Number of results to skip for pagination. Defaults to 0.

        Returns:
         - json_schemas.StationsJSON | json_schemas.RateLimitJSON: Station information or rate limit message.

        Raises:
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.
        """  # noqa: E501

        return cast(
            json_schemas.StationsJSON | json_schemas.RateLimitJSON,
            await self._make_request(
                f"{self.ENDPOINT}/stations",
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
        sortfield: parameter_schemas.Sortfield = "id",
        sortorder: parameter_schemas.Sortorder = "asc",
        limit: int = 25,
        offset: int = 0,
        includemetadata: bool = True,
    ) -> json_schemas.DataJSON | json_schemas.RateLimitJSON:
        """
        Query actual climate data based on specified parameters. Porviding a string or list of strings of amersand separaated values is also supported.


        Args:
         - datasetid (str): Required. The dataset ID to query.
         - startdate (str): Required. Beginning of date range in 'YYYY-MM-DD' format.
         - enddate (str): Required. End of date range in 'YYYY-MM-DD' format.
         - datatypeid (str | list[str], optional): Filter by data type ID(s). Defaults to "".
         - locationid (str | list[str], optional): Filter by location ID(s). Defaults to "".
         - stationid (str | list[str], optional): Filter by station ID(s). Defaults to "".
         - units (parameter_schemas.Units, optional): Unit conversion ("standard" or "metric"). Defaults to "".
         - sortfield (parameter_schemas.Sortfield, optional): Field to sort results by. Defaults to "id".
         - sortorder (parameter_schemas.Sortorder, optional): Direction of sort ("asc" or "desc"). Defaults to "asc".
         - limit (int, optional): Maximum number of results to return. Defaults to 25.
         - offset (int, optional): Number of results to skip for pagination. Defaults to 0.
         - includemetadata (bool, optional): Whether to include metadata in the response. Defaults to True.

        Returns:
         - json_schemas.DataJSON | json_schemas.RateLimitJSON: Climate data or rate limit message.

        Raises:
         - ValueError: If 'limit' parameter exceeds 1000.
         - aiohttp.ClientResponseError: If the request fails.
         - `MissingTokenError`: If the client header `token`, attribute `token`, or parameter `token_parameter` are all not provided.

        Notes:
         - Annual and monthly data will be limited to a 10-year range.
         - Other data will be limited to a 1-year range.
         - Not following these guidelines will raise a `ClientResponseError`. The reason for this rather than raising an exception prior to the 'GET' reqest is because knowing whether a datatype is hourly, monthly, or annually (and therefore the allowed time domain) requires an additional request.
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
            token_parameter=token_parameter,
        )

        return cast(
            json_schemas.DataJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    def close(self):
        """
        Close the aiohttp session if it is open.

        This method should be called when the client is no longer needed to properly
        release resources associated with the HTTP session.

        Note: This method works both in an async context and outside of an async context.
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
