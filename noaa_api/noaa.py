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

    async def make_request(
        self, url: str, parameters: parameter_schemas.DatasetsParameters
    ):
        async with self.seconds_request_limiter, self.daily_request_limiter:
            return self.aiohttp_session.get(
                url, params=cast(Mapping[str, str | int], parameters)
            )

    def close(self):
        _ = self.aiohttp_session.close()

    def __del__(self):
        self.close()
