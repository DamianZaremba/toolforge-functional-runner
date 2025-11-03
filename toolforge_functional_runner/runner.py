import dataclasses
import enum
import logging
import posixpath
import re
from pathlib import PosixPath

from paramiko.client import SSHClient

from toolforge_functional_runner.executor import run_command_as_tool

logger = logging.getLogger(__name__)


class TestStatus(enum.IntEnum):
    SUCCESS = 0
    FAILURE = 1
    SKIPPED = 2


@dataclasses.dataclass(frozen=True)
class TestResult:
    name: str
    status: TestStatus
    duration: int | None
    extra: str | None


def get_test_suites(client: SSHClient, tool_name: str, path: PosixPath) -> dict[str, list[str]]:
    stdout, stderr, exit_status = run_command_as_tool(
        client, tool_name, f'find "{path.as_posix()}" -type f -iname "*.bats"', True
    )

    suites = {}
    for line in stdout.splitlines():
        relative_path = PosixPath(line).absolute().relative_to(path.absolute())
        suite_name = relative_path.parts[0]
        if suite_name not in suites:
            suites[suite_name] = []

        component_name = posixpath.join(*relative_path.parts[1:-1])
        if component_name not in suites[suite_name]:
            suites[suite_name].append(component_name)
    return dict(suites)


def parse_tap_result(line: str, suite_name: str, component_name: str) -> TestResult | None:
    extra = None
    if " # " in line:
        line, extra = line.split(" # ", 1)

    if line.startswith("not ok "):
        status = TestStatus.FAILURE
        line = line.removeprefix("not ok ")
    else:
        line = line.removeprefix("ok ")
        status = TestStatus.SKIPPED if extra and "skip remaining tests" in extra else TestStatus.SUCCESS

    _, description = line.strip().split(" ", 1)

    test_name, duration = None, None
    if matches := re.match(r"^(.+) in ([0-9]+)ms$", description):
        test_name = matches.group(1)
        duration = int(matches.group(2))
    else:
        test_name = description

    if test_name:
        return TestResult(
            name=test_name,
            status=status,
            extra=extra,
            duration=duration,
        )
    return None


def process_test_results(suite_name: str, component_name: str, lines: list[str]) -> list[TestResult]:
    results = []
    for x, line in enumerate(lines):
        # First line is the number of tests e.g. `1..18`
        if x == 0:
            continue

        # Output from the jobs is pre-fixed with a comment, so just dump it directly back to the user
        if line.startswith("#"):
            logger.error(line.strip())
            continue

        logger.info(line.strip())
        if result := parse_tap_result(line, suite_name, component_name):
            results.append(result)
        else:
            # We didn't handle it
            logger.error(f"Failed to parse output: {line}")

    return results


def run_test_suite(
    client: SSHClient, tool_name: str, venv_path: PosixPath, repo_path: PosixPath, suite_name: str, component_name: str
) -> list[TestResult]:
    command = (
        f'PATH="{(venv_path / "bin").as_posix()}:$PATH" TEST_TOOL_UID="{tool_name}" '
        f"bats_core_pkg "
        "--formatter tap "
        "--recursive "
        "--timing "
        "--verbose-run "
        "--setup-suite-file "
        f'{(repo_path / "setup_suite.bash").as_posix()} '
        f"{(repo_path / suite_name).as_posix()} "
        f"--filter-tags {component_name}"
    )
    logger.debug(f"Running test suite via {command}")

    stdout, _, _ = run_command_as_tool(client, tool_name, command)
    return process_test_results(suite_name, component_name, stdout.splitlines())
