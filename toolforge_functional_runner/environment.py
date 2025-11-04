import logging
from pathlib import PosixPath

from paramiko.client import SSHClient

from toolforge_functional_runner.config import DeploymentRepo
from toolforge_functional_runner.executor import directory_exists, run_command_as_tool

logger = logging.getLogger(__name__)


def setup_environment_repo(client: SSHClient, tool_name: str, target_path: PosixPath, repo: DeploymentRepo) -> None:
    if directory_exists(client, tool_name, target_path):
        logger.info(f"Found existing repo directory at {target_path}")
    else:
        logger.info(f"Cloning {repo.url} into {target_path}")
        run_command_as_tool(client, tool_name, f'git clone "{repo.url}" "{target_path.as_posix()}"', True)


def update_environment_repo(client: SSHClient, tool_name: str, target_path: PosixPath, repo: DeploymentRepo) -> None:
    stdout, _, _ = run_command_as_tool(
        client, tool_name, f'git -C "{target_path.as_posix()}" remote get-url origin', True
    )
    if stdout.strip() != repo.url:
        logger.info(f"Changing repo URL {stdout} -> {repo.url}")
        run_command_as_tool(
            client, tool_name, f'git -C "{target_path.as_posix()}" remote set-url origin "{repo.url}"', True
        )

    logger.info("Fetching latest changes")
    run_command_as_tool(
        client,
        tool_name,
        f'git -C "{target_path.as_posix()}" fetch && ' f'git -C "{target_path.as_posix()}" reset --hard FETCH_HEAD',
        True,
    )

    stdout, _, _ = run_command_as_tool(
        client, tool_name, f'git -C "{target_path.as_posix()}" rev-parse --abbrev-ref HEAD', True
    )
    if stdout.strip() != repo.branch:
        logger.info(f"Changing repo branch {stdout} -> {repo.branch}")
        run_command_as_tool(client, tool_name, f'git -C "{target_path.as_posix()}" switch "{repo.branch}"', True)


def setup_environment_venv(client: SSHClient, tool_name: str, target_path: PosixPath) -> None:
    if directory_exists(client, tool_name, target_path):
        logger.info(f"Found existing venv directory at {target_path}")
    else:
        logger.info(f"Running container to create venv at {target_path}")
        run_command_as_tool(
            client,
            tool_name,
            (
                "toolforge jobs run "
                "--image=python3.13 "
                "--mount=all "
                f'--command="python3 -m venv --copies {target_path.as_posix()}" '
                "--wait=60 "
                "--no-filelog "
                "create-venv"
            ),
            True,
        )


def update_environment_venv(client: SSHClient, tool_name: str, target_path: PosixPath) -> None:
    logger.info(f"Installing bats in venv at {target_path}")
    run_command_as_tool(
        client,
        tool_name,
        (
            f'source {(target_path / "bin" / "activate").as_posix()} && '
            f"python -m pip install --upgrade bats-core-pkg"
        ),
        True,
    )


def cleanup_tool_environment(client: SSHClient, tool_name: str, project_path: PosixPath) -> None:
    logger.info(f"Cleaning dangling files in {project_path}")
    run_command_as_tool(
        client,
        tool_name,
        f'find "{project_path.as_posix()}" -type f -iname "*.err" -delete;'
        f'find "{project_path.as_posix()}" -type f -iname "*.out" -delete; '
        f'find "{project_path.as_posix()}" -type f -iname "*.yaml" -delete; '
        f'rm -f "{(project_path / "status").as_posix()}"'
    )


def setup_tool_environment(client: SSHClient, tool_name: str, project_path: PosixPath) -> None:
    logger.info(f"Ensuring public_html exists in {project_path}")
    run_command_as_tool(
        client,
        tool_name,
        f'mkdir -p "{(project_path / "public_html").as_posix()}"',
        True,
    )
