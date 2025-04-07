import asyncio
import json
import os
from typing import cast

import dotenv

import manual_tests.log_setup as log_setup
import noaa_api.json_responses as json_responses
import noaa_api.noaa as noaa
from manual_tests.validate_json import validate_test

logger = log_setup.get_logger(__name__, "logs/datatypes.log")

DATATYPES_RESPONSE_SAMPLE_PATH: str = "sample_responses/datatypes/datatypes.json"
DATATYPES_ID_RESPONSE_SAMPLE_PATH: str = "sample_responses/datatypes/datatypes-id.json"
DATATYPES_RATELIMIT_RESPONSE_SAMPLE_PATH: str = (
    "sample_responses/datatypes-rate-limit.json"
)

os.makedirs("sample_responses", exist_ok=True)
os.makedirs("sample_responses/datatypes", exist_ok=True)


def pull_datatypes(client: noaa.NOAAClient | None = None):
    token = dotenv.dotenv_values().get("token", None)

    if token is None:
        logger.info("Token (key: `token`) not found in .env file. Skipping data pull")
        return

    logger.info("Token (key: `token`) found in .env file. Pulling data.")
    client = noaa.NOAAClient(token=token) if client is None else client

    response = cast(json_responses.DatatypesJSON, asyncio.run(client.get_datatypes()))

    with open(DATATYPES_RESPONSE_SAMPLE_PATH, "w") as f:
        json.dump(response, f, indent=4)

    sample_id: str = next(iter(response["results"]))["id"]

    response_id = asyncio.run(client.get_datatype_by_id(sample_id))

    with open(DATATYPES_ID_RESPONSE_SAMPLE_PATH, "w") as f:
        json.dump(response_id, f, indent=4)

    logger.info("Data pull complete.")

    client.close()


if __name__ == "__main__":
    pull_datatypes()
    validate_test(
        logger,
        DATATYPES_RESPONSE_SAMPLE_PATH,
        DATATYPES_ID_RESPONSE_SAMPLE_PATH,
        DATATYPES_RATELIMIT_RESPONSE_SAMPLE_PATH,
        json_responses.DatatypesJSON,
        json_responses.DatatypeIDJSON,
        json_responses.RateLimitJSON,
    )
