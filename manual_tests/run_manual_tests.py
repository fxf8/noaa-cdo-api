import asyncio
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.style import Style

import manual_tests.log_setup as log_setup

logger = log_setup.get_logger(__name__, "logs/run_manual_tests.log")
console = Console()

MANUAL_TESTS = [
    "data.py",
    "datacategories.py",
    "datasets.py",
    "datatypes.py",
    "locationcategories.py",
    "locations.py",
    "stations.py",
]


def create_test_panel(title: str, content: str, success: bool) -> Panel:
    """Create a fancy panel for test output."""
    style = Style(color="green" if success else "red")
    # title_style = Style(color="green" if success else "red", bold=True)
    return Panel(
        content,
        title=title,
        title_align="left",
        border_style=style,
        style=style,
        padding=(1, 2),
    )


async def run_tests():
    manual_tests_dir = Path(__file__).parent
    python_executable = sys.executable
    total_tests = len(MANUAL_TESTS)
    passed_tests = 0

    console.print("\n[bold cyan]🧪 NOAA API Manual Tests[/bold cyan]")
    console.print("=" * 50 + "\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for i, test_file in enumerate(MANUAL_TESTS, 1):
            test_path = manual_tests_dir / test_file
            task_id = progress.add_task(f"Running {test_file}...", total=None)
            logger.info(f"Running test: {test_file}")

            try:
                process = await asyncio.create_subprocess_exec(
                    python_executable,
                    str(test_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()
                progress.remove_task(task_id)

                output = ""
                if stdout:
                    stdout_str = stdout.decode()
                    logger.info(f"[{test_file}] stdout:\n{stdout_str}")
                    output += f"[white]stdout:[/white]\n{stdout_str}\n"

                if stderr:
                    stderr_str = stderr.decode()
                    logger.error(f"[{test_file}] stderr:\n{stderr_str}")
                    output += f"[red]stderr:[/red]\n{stderr_str}\n"

                success = process.returncode == 0
                if success:
                    passed_tests += 1
                    logger.info(f"Test {test_file} completed successfully")
                else:
                    logger.error(
                        f"Test {test_file} failed with return code {process.returncode}"
                    )

                console.print(
                    create_test_panel(
                        f"Test {i}/{total_tests}: {test_file}",
                        output or "No output",
                        success,
                    )
                )

            except Exception as e:
                progress.remove_task(task_id)
                error_msg = f"Error running {test_file}: {e}"
                logger.error(error_msg)
                console.print(
                    create_test_panel(
                        f"Test {i}/{total_tests}: {test_file}",
                        f"[red]{error_msg}[/red]",
                        False,
                    )
                )

            # Wait 1 second before running the next test
            if i < total_tests:
                await asyncio.sleep(1)

    # Print summary
    console.print("\n" + "=" * 50)
    summary_style = "green" if passed_tests == total_tests else "red"
    console.print(
        f"\n[bold {summary_style}]Test Summary: {passed_tests}/{total_tests} tests passed[/bold {summary_style}]"  # noqa: E501
    )


if __name__ == "__main__":
    asyncio.run(run_tests())
