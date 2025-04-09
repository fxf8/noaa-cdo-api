# pyright: reportAny=false
# pyright: reportExplicitAny=false

import inspect
import json
import logging
import os
from collections.abc import Mapping, Sequence
from types import UnionType
from typing import Any, NotRequired, cast, get_args, get_origin


def value_matches_type(data: Any, typeddict_class: type) -> bool:
    """
    Recursively validates that the given data conforms to the structure defined by the TypedDict class.

    Args:
        data: The data to validate (typically parsed from JSON)
        typeddict_class: A class that implements TypedDict

    Returns:
        bool: True if the data matches the TypedDict schema, False otherwise
    """  # noqa: E501

    type_origin: type | None = get_origin(typeddict_class)
    type_args: tuple[type, ...] | None = get_args(typeddict_class)

    if type_origin is UnionType:
        return any(value_matches_type(data, type_arg) for type_arg in type_args)

    if inspect.isclass(typeddict_class) and hasattr(typeddict_class, "__annotations__"):
        if not isinstance(data, Mapping):
            return False

        for key, value in cast(Mapping[str, object], data).items():
            if key not in typeddict_class.__annotations__:
                return False

            if not value_matches_type(value, typeddict_class.__annotations__[key]):
                return False

        return True

    if (
        isinstance(typeddict_class, Mapping)
        or isinstance(type_origin, type)
        and issubclass(type_origin, Mapping)
    ):
        if not issubclass(data, Mapping):
            return False

        if len(type_args) != 2:
            return True

        key_type, value_type = type_args

        for key, value in cast(Mapping[object, object], data).items():
            if not value_matches_type(key, key_type):
                return False

            if not value_matches_type(value, value_type):
                return False

        return True

    if (
        isinstance(typeddict_class, Sequence)
        or isinstance(type_origin, type)
        and issubclass(type_origin, Sequence)
    ):
        if not isinstance(data, Sequence):
            return False

        if len(type_args) == 0:
            return True

        sequence_type = type_args[0]

        return all(value_matches_type(item, sequence_type) for item in data)

    if typeddict_class is NotRequired or type_origin is NotRequired:
        if len(type_args) == 0:
            return True

        if len(type_args) == 1:
            return value_matches_type(data, type_args[0])

    return isinstance(data, typeddict_class)  # Neither Mapping, TypedDict, or Sequence


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
        with open(sample_path) as f:
            json_response = json.load(f)

        assert value_matches_type(json_response, general_response_schema)

        logger.info(f"{sample_path} is valid.")

    else:
        logger.info(f"{sample_path} does not exist. Skipping validation.")

    if id_sample_path is not None and id_response_schema is not None:
        logger.info(f"Validating {id_sample_path}")

        if os.path.exists(id_sample_path):
            logger.info(f"{id_sample_path} exists. Validating...")
            with open(id_sample_path) as f:
                id_response = json.load(f)

            assert value_matches_type(id_response, id_response_schema)

            logger.info(f"{id_sample_path} is valid.")

        else:
            logger.info(f"{id_sample_path} does not exist. Skipping validation.")

    if ratelimit_path is not None and ratelimit_response_schema is not None:
        logger.info(f"Validating {ratelimit_path}")

        if os.path.exists(ratelimit_path):
            logger.info(f"{ratelimit_path} exists. Validating...")
            with open(ratelimit_path) as f:
                ratelimit_response = json.load(f)

            assert value_matches_type(ratelimit_response, ratelimit_response_schema)

            logger.info(f"{ratelimit_path} is valid.")

        else:
            logger.info(
                f"{ratelimit_path} does not exist. Skipping validation."  # noqa: E501
            )
