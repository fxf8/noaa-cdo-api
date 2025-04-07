import asyncio
import subprocess
import sys
from pathlib import Path

import manual_tests.log_setup as log_setup

logger = log_setup.get_logger(__name__, "logs/run_manual_tests.log")

MANUAL_TESTS = [
    "data.py",
    "datacategories.py",
    "datasets.py",
    "datatypes.py",
    "locationcategories.py",
    "locations.py",
    "stations.py",
]


async def run_tests():
    manual_tests_dir = Path(__file__).parent
    python_executable = sys.executable

    for test_file in MANUAL_TESTS:
        test_path = manual_tests_dir / test_file
        logger.info(f"Running test: {test_file}")

        try:
            process = await asyncio.create_subprocess_exec(
                python_executable,
                str(test_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if stdout:
                logger.info(f"[{test_file}] stdout:\n{stdout.decode()}")
            if stderr:
                logger.error(f"[{test_file}] stderr:\n{stderr.decode()}")

            if process.returncode != 0:
                logger.error(f"Test {test_file} failed with return code {process.returncode}")
            else:
                logger.info(f"Test {test_file} completed successfully")

        except Exception as e:
            logger.error(f"Error running {test_file}: {e}")

        # Wait 1 second before running the next test
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_tests())
