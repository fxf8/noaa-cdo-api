import asyncio
import json
import os
from typing import cast

import dotenv

import manual_tests.log_setup as log_setup
import noaa_cdo_api.json_responses as json_responses
import noaa_cdo_api.noaa as noaa
from manual_tests.validate_json import validate_test

logger = log_setup.get_logger(__name__, "logs/stations.log")

STATIONS_RESPONSE_SAMPLE_PATH: str = "sample_responses/stations/stations.json"
STATIONS_ID_RESPONSE_SAMPLE_PATH: str = "sample_responses/stations/stations-id.json"
STATIONS_RATELIMIT_RESPONSE_SAMPLE_PATH: str = (
    "sample_responses/stations-rate-limit.json"
)

os.makedirs("sample_responses", exist_ok=True)
os.makedirs("sample_responses/stations", exist_ok=True)


async def pull_stations(client: noaa.NOAAClient | None = None):
    token = dotenv.dotenv_values().get("token", None)

    if token is None:
        logger.info("Token (key: `token`) not found in .env file. Skipping data pull")
        return

    logger.info("Token (key: `token`) found in .env file. Pulling data.")
    client = noaa.NOAAClient(token=token) if client is None else client

    async with client:
        response = cast(json_responses.StationsJSON, await client.get_stations())

        with open(STATIONS_RESPONSE_SAMPLE_PATH, "w") as f:
            json.dump(response, f, indent=4)

        sample_id: str = next(iter(response["results"]))["id"]

        response_id = await client.get_station_by_id(sample_id)

        with open(STATIONS_ID_RESPONSE_SAMPLE_PATH, "w") as f:
            json.dump(response_id, f, indent=4)

        logger.info("Data pull complete.")


if __name__ == "__main__":
    asyncio.run(pull_stations())
    validate_test(
        logger,
        STATIONS_RESPONSE_SAMPLE_PATH,
        STATIONS_ID_RESPONSE_SAMPLE_PATH,
        STATIONS_RATELIMIT_RESPONSE_SAMPLE_PATH,
        json_responses.StationsJSON,
        json_responses.StationIDJSON,
        json_responses.RateLimitJSON,
    )
