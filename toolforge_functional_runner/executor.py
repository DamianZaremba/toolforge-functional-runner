import logging
from contextlib import contextmanager
from pathlib import PosixPath
from typing import Tuple

import paramiko
from paramiko.client import SSHClient
from paramiko.pkey import PKey

from toolforge_functional_runner.config import Config

logger = logging.getLogger(__name__)


def run_command_as_tool(
    client: SSHClient, tool_name: str, command: str, raise_on_failure: bool = False
) -> Tuple[str, str, int]:
    prefixed_command = "/usr/bin/sudo " f"-niu tools.{tool_name} " f"bash -c '{command}'"
    logger.debug(f"Executing: {prefixed_command}")

    _, _stdout, _stderr = client.exec_command(prefixed_command)
    stdout = _stdout.read().decode().strip()
    stderr = _stderr.read().decode().strip()
    status = _stdout.channel.recv_exit_status()
    logger.debug(f"Command result: {prefixed_command}\nstdout: {stdout}\nstderr: {stdout}\nstatus: {status}")

    if raise_on_failure and status != 0:
        logger.error(f"Command failed: {prefixed_command}\nstdout: {stdout}\nstderr: {stdout}\nstatus: {status}")
        raise RuntimeError("Failed command")
    return stdout, stderr, status


def directory_exists(client: SSHClient, tool_name: str, path: PosixPath) -> bool:
    _, _, exit_status = run_command_as_tool(client, tool_name, f'test -d "{path.as_posix()}"')
    return exit_status == 0


def file_exists(client: SSHClient, tool_name: str, path: PosixPath) -> bool:
    _, _, exit_status = run_command_as_tool(client, tool_name, f'test -f "{path.as_posix()}"')
    return exit_status == 0


@contextmanager
def ssh_connection(config: Config, ssh_key: str | None):
    with paramiko.client.SSHClient() as client:
        for host_key in config.target.ssh_fingerprints:
            client.get_host_keys().add(config.target.host, host_key.get_name(), host_key)

        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(
            config.target.host,
            username=config.target.user,
            pkey=PKey.from_path(ssh_key) if ssh_key else None,
            look_for_keys=False,
        )

        yield client
