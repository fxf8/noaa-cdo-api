import logging
import os
import pathlib
import sys


def get_logger(
    name: str,
    log_path: str,
):
    log_directory: pathlib.Path = pathlib.Path(log_path).parent

    os.makedirs(log_directory, exist_ok=True)
    open(log_path, "w").close()

    logger = logging.getLogger(name)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path),
        ],
    )

    return logger
