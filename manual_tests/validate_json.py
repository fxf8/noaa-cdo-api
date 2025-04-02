# pyright: reportAny=false

import json


def validate_json_file(file_path: str, schema: type) -> bool:
    """Reads a JSON file and checks if it matches the given TypedDict schema."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):  # Ensure top-level structure is a dictionary
            return False

        # Check if all required keys exist and have correct types
        for key, expected_type in schema.__annotations__.items():
            if key not in data or not isinstance(data[key], expected_type):
                return False

        return True
    except (json.JSONDecodeError, FileNotFoundError):
        return False
