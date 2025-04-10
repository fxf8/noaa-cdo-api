import asyncio
import json
import os
from typing import cast

import dotenv

import manual_tests.log_setup as log_setup
import noaa_cdo_api.json_responses as json_responses
import noaa_cdo_api.noaa as noaa
from manual_tests.validate_json import validate_test

logger = log_setup.get_logger(__name__, "logs/data.log")

DATA_RESPONSE_SAMPLE_PATH: str = "sample_responses/data/data.json"
DATA_RATELIMIT_RESPONSE_SAMPLE_PATH: str = "sample_responses/data-rate-limit.json"

os.makedirs("sample_responses", exist_ok=True)
os.makedirs("sample_responses/data", exist_ok=True)


async def pull_data(client: noaa.NOAAClient | None = None):
    token = dotenv.dotenv_values().get("token", None)

    if token is None:
        logger.info("Token (key: `token`) not found in .env file. Skipping data pull")
        return

    logger.info("Token (key: `token`) found in .env file. Pulling data.")
    client = noaa.NOAAClient(token=token) if client is None else client

    async with client:
        # For data endpoint, we need some parameters to make a valid request
        # Using some sample values that should work
        response = cast(
            json_responses.DataJSON,
            await client.get_data(
                datasetid="GHCND",
                startdate="2024-01-01",
                enddate="2024-01-02",
                limit=10,
            ),
        )

        with open(DATA_RESPONSE_SAMPLE_PATH, "w") as f:
            json.dump(response, f, indent=4)

        logger.info("Data pull complete.")


if __name__ == "__main__":
    asyncio.run(pull_data())
    validate_test(
        logger,
        DATA_RESPONSE_SAMPLE_PATH,
        None,  # No ID endpoint for data
        DATA_RATELIMIT_RESPONSE_SAMPLE_PATH,
        json_responses.DataJSON,
        None,  # No ID endpoint for data
        json_responses.RateLimitJSON,
    )
