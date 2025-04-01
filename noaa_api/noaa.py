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
        if (
            parameters is not None
            and "limit" in parameters
            and parameters["limit"] > 1000
        ):
            raise ValueError("Parameter 'limit' must be less than or equal to 1000")

        async with self.seconds_request_limiter, self.daily_request_limiter:
            async with self.aiohttp_session.get(
                url, params=cast(Mapping[str, str], parameters)
            ) as response:
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
        _ = self.aiohttp_session.close()

    def __del__(self):
        self.close()
