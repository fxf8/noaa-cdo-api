from collections.abc import Mapping
from typing import ClassVar, cast
import aiohttp
import aiolimiter

import noaa_api.json_schemas as json_schemas
import noaa_api.parameter_schemas as parameter_schemas


class NOAAClient:
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
        async with self.seconds_request_limiter, self.daily_request_limiter:
            async with self.aiohttp_session.get(
                url, params=cast(Mapping[str, str], parameters)
            ) as response:
                response.raise_for_status()
                return response

    async def get_datasets(
        self,
        id: str | None = None,
        parameters: parameter_schemas.DatasetsParameters | None = None,
    ) -> json_schemas.DatasetsJSON | json_schemas.RateLimitJSON:
        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/datasets"
            if id is None
            else f"{self.ENDPOINT}/datasets/{id}",
            parameters=parameters,
        )

        return cast(
            json_schemas.DatasetsJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_data_categories(
        self,
        id: str | None = None,
        parameters: parameter_schemas.DatacategoriesParameters | None = None,
    ) -> json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON:
        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/datacategories"
            if id is None
            else f"{self.ENDPOINT}/datacategories/{id}",
            parameters=parameters,
        )

        return cast(
            json_schemas.DatacategoriesJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_datatypes(
        self,
        id: str | None = None,
        parameters: parameter_schemas.DatatypesParameters | None = None,
    ) -> json_schemas.DatatypesJSON | json_schemas.RateLimitJSON:
        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/datatypes"
            if id is None
            else f"{self.ENDPOINT}/datatypes/{id}",
            parameters=parameters,
        )

        return cast(
            json_schemas.DatatypesJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_location_categories(
        self,
        id: str | None = None,
        parameters: parameter_schemas.LocationcategoriesParameters | None = None,
    ) -> json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON:
        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/locationcategories"
            if id is None
            else f"{self.ENDPOINT}/locationcategories/{id}",
            parameters=parameters,
        )

        return cast(
            json_schemas.LocationcategoriesJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_locations(
        self,
        id: str | None = None,
        parameters: parameter_schemas.LocationsParameters | None = None,
    ) -> json_schemas.LocationsJSON | json_schemas.RateLimitJSON:
        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/locations"
            if id is None
            else f"{self.ENDPOINT}/locations/{id}",
            parameters=parameters,
        )

        return cast(
            json_schemas.LocationsJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_stations(
        self,
        id: str | None = None,
        parameters: parameter_schemas.StationsParameters | None = None,
    ) -> json_schemas.StationsJSON | json_schemas.RateLimitJSON:
        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/stations"
            if id is None
            else f"{self.ENDPOINT}/stations/{id}",
            parameters=parameters,
        )

        return cast(
            json_schemas.StationsJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    async def get_data(
        self,
        id: str | None = None,
        parameters: parameter_schemas.DataParameters | None = None,
    ) -> json_schemas.DataJSON | json_schemas.RateLimitJSON:
        client_response: aiohttp.ClientResponse = await self._make_request(
            f"{self.ENDPOINT}/data" if id is None else f"{self.ENDPOINT}/data/{id}",
            parameters=parameters,
        )

        return cast(
            json_schemas.DataJSON | json_schemas.RateLimitJSON,
            await client_response.json(),
        )

    def close(self):
        _ = self.aiohttp_session.close()

    def __del__(self):
        self.close()
