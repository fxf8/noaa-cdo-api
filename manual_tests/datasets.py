import asyncio
import json
import os
from typing import cast

import dotenv

import manual_tests.log_setup as log_setup
import noaa_api.json_responses as json_responses
import noaa_api.noaa as noaa
from manual_tests.validate_json import validate_json_file

logger = log_setup.get_logger(__name__, "logs/datasets.log")

DATASETS_RESPONSE_SAMPLE_PATH: str = "sample_responses/datasets.json"
DATASETS_ID_RESPONSE_SAMPLE_PATH: str = "sample_responses/datasets-id.json"
DATASETS_RATELIMIT_RESPONSE_SAMPLE_PATH: str = (
    "sample_responses/datasets-rate-limit.json"
)

os.makedirs("sample_responses", exist_ok=True)


def pull_datasets(client: noaa.NOAAClient | None = None):
    token = dotenv.dotenv_values().get("token", None)

    if token is None:
        logger.info("Token (key: `token`) not found in .env file. Skipping data pull")

    if token is not None:
        logger.info("Token (key: `token`) found in .env file. Pulling data.")
        client = noaa.NOAAClient(token=token) if client is None else client

        # Assume response is noaa.
        response = cast(json_responses.DatasetsJSON, asyncio.run(client.get_datasets()))

        with open(DATASETS_RESPONSE_SAMPLE_PATH, "w") as f:
            json.dump(response, f, indent=4)

        sample_id: str = next(iter(response["results"]))["id"]

        response_id = asyncio.run(client.get_datasets(id=sample_id))

        with open(DATASETS_ID_RESPONSE_SAMPLE_PATH, "w") as f:
            json.dump(response_id, f, indent=4)

        logger.info("Data pull complete.")


def validate_datasets():
    logger.info(f"Validating {DATASETS_RESPONSE_SAMPLE_PATH}")

    if os.path.exists(DATASETS_RESPONSE_SAMPLE_PATH):
        logger.info(f"{DATASETS_RESPONSE_SAMPLE_PATH} exists. Validating...")

        assert validate_json_file(
            DATASETS_RESPONSE_SAMPLE_PATH, json_responses.DatasetsJSON
        )

        logger.info(f"{DATASETS_RESPONSE_SAMPLE_PATH} is valid.")

    else:
        logger.info(
            f"{DATASETS_RESPONSE_SAMPLE_PATH} does not exist. Skipping validation."
        )

    logger.info(f"Validating {DATASETS_ID_RESPONSE_SAMPLE_PATH}")

    if os.path.exists(DATASETS_ID_RESPONSE_SAMPLE_PATH):
        logger.info(f"{DATASETS_ID_RESPONSE_SAMPLE_PATH} exists. Validating...")

        assert validate_json_file(
            DATASETS_ID_RESPONSE_SAMPLE_PATH, json_responses.DatasetIDJSON
        )

        logger.info(f"{DATASETS_ID_RESPONSE_SAMPLE_PATH} is valid.")

    else:
        logger.info(
            f"{DATASETS_ID_RESPONSE_SAMPLE_PATH} does not exist. Skipping validation."
        )

    logger.info(f"Validating {DATASETS_RATELIMIT_RESPONSE_SAMPLE_PATH}")

    if os.path.exists(DATASETS_RATELIMIT_RESPONSE_SAMPLE_PATH):
        logger.info(f"{DATASETS_RATELIMIT_RESPONSE_SAMPLE_PATH} exists. Validating...")

        assert validate_json_file(
            DATASETS_RATELIMIT_RESPONSE_SAMPLE_PATH, json_responses.RateLimitJSON
        )

        logger.info(f"{DATASETS_RATELIMIT_RESPONSE_SAMPLE_PATH} is valid.")

    else:
        logger.info(
            f"{DATASETS_RATELIMIT_RESPONSE_SAMPLE_PATH} does not exist. Skipping validation."  # noqa: E501
        )


if __name__ == "__main__":
    pull_datasets()
    validate_datasets()
