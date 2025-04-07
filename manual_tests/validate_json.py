# pyright: reportAny=false
# pyright: reportExplicitAny=false

import json
import logging
import os
from typing import Any, Union, get_args, get_origin  # pyright: ignore[reportDeprecated]


def validate_typeddict(json_object: Any, schema: type) -> bool:
    origin = get_origin(schema)
    args = get_args(schema)

    if origin is list:
        if not isinstance(json_object, list):
            return False
        item_type = args[0]
        return all(validate_typeddict(item, item_type) for item in json_object)  # pyright: ignore[reportUnknownVariableType]

    elif origin is dict:
        if not isinstance(json_object, dict):
            return False
        key_type, value_type = args
        return all(
            isinstance(k, key_type) and validate_typeddict(v, value_type)
            for k, v in json_object.items()  # pyright: ignore[reportUnknownVariableType]
        )

    elif origin is Union:  # pyright: ignore[reportDeprecated]
        return any(validate_typeddict(json_object, arg) for arg in args)

    elif isinstance(json_object, dict) and hasattr(schema, "__annotations__"):
        for key, value_type in schema.__annotations__.items():
            if key not in json_object:
                return False
            if not validate_typeddict(json_object[key], value_type):
                return False
        return True

    else:
        return isinstance(json_object, schema)


def validate_json_file(file_path: str, schema: type) -> bool:
    """Reads a JSON file and checks if it matches the given TypedDict schema."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return validate_typeddict(data, schema)

    except (json.JSONDecodeError, FileNotFoundError):
        return False


def validate_test(
    logger: logging.Logger,
    sample_path: str,
    id_sample_path: str | None,
    ratelimit_path: str | None,
    general_response_schema: type,
    id_response_schema: type | None,
    ratelimit_response_schema: type | None,
):
    logger.info(f"Validating {sample_path}")

    if os.path.exists(sample_path):
        logger.info(f"{sample_path} exists. Validating...")

        assert validate_json_file(sample_path, general_response_schema)

        logger.info(f"{sample_path} is valid.")

    else:
        logger.info(f"{sample_path} does not exist. Skipping validation.")

    if id_sample_path is not None:
        logger.info(f"Validating {id_sample_path}")

        if os.path.exists(id_sample_path):
            logger.info(f"{id_sample_path} exists. Validating...")

            assert validate_json_file(id_sample_path, id_response_schema)

            logger.info(f"{id_sample_path} is valid.")

        else:
            logger.info(f"{id_sample_path} does not exist. Skipping validation.")

    if ratelimit_path is not None:
        logger.info(f"Validating {ratelimit_path}")

        if os.path.exists(ratelimit_path):
            logger.info(f"{ratelimit_path} exists. Validating...")

            assert validate_json_file(ratelimit_path, ratelimit_response_schema)

            logger.info(f"{ratelimit_path} is valid.")

        else:
            logger.info(
                f"{ratelimit_path} does not exist. Skipping validation."  # noqa: E501
            )
