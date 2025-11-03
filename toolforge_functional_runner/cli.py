#!/usr/bin/env python3
import functools
import logging
import sys
import threading
import time

import click
from prometheus_client import start_http_server

from toolforge_functional_runner.config import Config
from toolforge_functional_runner.environment import (
    setup_environment_repo,
    update_environment_repo,
    setup_environment_venv,
    update_environment_venv,
    cleanup_tool_environment,
)
from toolforge_functional_runner.executor import ssh_connection
from toolforge_functional_runner.metrics import registry, update_run_metrics, RunStatus, update_test_suite_metrics
from toolforge_functional_runner.runner import run_test_suite, get_test_suites

logger = logging.getLogger(__name__)


def _setup_environment(config: Config, ssh_key: str):
    with ssh_connection(config, ssh_key) as client:
        cleanup_tool_environment(client, config.environment.tool, config.environment.project)
        setup_environment_repo(client, config.environment.tool, config.environment.repo, config.repo)
        update_environment_repo(client, config.environment.tool, config.environment.repo, config.repo)
        setup_environment_venv(client, config.environment.tool, config.environment.venv)
        update_environment_venv(client, config.environment.tool, config.environment.venv)


def _execute_run(config: Config, ssh_key: str, update_environment: bool):
    with ssh_connection(config, ssh_key) as client:
        if update_environment:
            cleanup_tool_environment(client, config.environment.tool, config.environment.project)
            update_environment_repo(client, config.environment.tool, config.environment.repo, config.repo)

        test_suites = get_test_suites(client, config.environment.tool, config.environment.repo / config.repo.entrypoint)
        for suite_name, suite_components in test_suites.items():
            if suite_name in config.environment.skip_suites:
                logger.debug(f"Skipping {suite_name} due to configuration")
                continue

            for component_name in suite_components:
                logger.info(f"Executing run for {suite_name} -> {component_name}")
                test_status, start_time = RunStatus.SUCCESS, time.time()
                try:
                    test_results = run_test_suite(
                        client,
                        config.environment.tool,
                        config.environment.venv,
                        config.environment.repo / config.repo.entrypoint,
                        suite_name,
                        component_name,
                    )
                except Exception as e:
                    logger.exception("Test execution failed", e)
                    test_status = RunStatus.FAILURE
                else:
                    if not all([test_result.status == RunStatus.SUCCESS for test_result in test_results]):
                        test_status = RunStatus.PARTIAL

                end_time = time.time()

                update_run_metrics(
                    suite_name,
                    component_name,
                    end_time - start_time,
                    test_status,
                )

                if test_status != RunStatus.FAILURE:
                    update_test_suite_metrics(suite_name, component_name, test_results)


@click.option("--interval", type=int, default=60, help="Time to wait between runs")
@click.option("--metrics-port", type=int, default=9515, help="Port to serve metrics on")
@click.option("--single-run/--no-single-run", help="Only execute 1 run then exit")
@click.option("--setup/--no-setup", default=True, help="Execute the setup logic")
@click.option("--ssh-key", help="Path to the SSH private key")
@click.option("--debug/--no-debug", type=bool, default=False, help="Enable debug level logging")
@click.command()
def run(interval: int, metrics_port: int, single_run: bool, setup: bool, debug: bool, ssh_key: str | None):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    config = Config()

    # On startup, ensure our environment is configured
    if setup:
        _setup_environment(config, ssh_key)

    # Start a basic http server for prometheus metrics
    prometheus_thread = threading.Thread(
        target=functools.partial(start_http_server, port=metrics_port, registry=registry), daemon=True
    )
    prometheus_thread.start()

    # Now execute the main loop
    first_execution = True
    while True:
        _execute_run(config, ssh_key, not first_execution)

        if single_run:
            break

        time.sleep(interval)
        first_execution = False

    prometheus_thread.join()


if __name__ == "__main__":
    run()
