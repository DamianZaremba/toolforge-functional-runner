import enum

from prometheus_client import CollectorRegistry, Gauge

from toolforge_functional_runner.runner import TestResult


class RunStatus(enum.IntEnum):
    SUCCESS = 0
    FAILURE = 1
    PARTIAL = 2


registry = CollectorRegistry()
toolforge_test_run_status = Gauge(
    "toolforge_test_run_status",
    "Status of the last test run",
    ["suite_name", "component_name"],
    registry=registry,
)
toolforge_test_run_duration = Gauge(
    "toolforge_test_run_duration",
    "Duration of the last test run",
    ["suite_name", "component_name"],
    registry=registry,
)

toolforge_test_run_test_status = Gauge(
    "toolforge_test_run_test_status",
    "Status of the last functional test run",
    ["suite_name", "component_name", "test_name"],
    registry=registry,
)
toolforge_test_run_test_duration = Gauge(
    "toolforge_test_run_test_duration",
    "Duration of the last functional test run",
    ["suite_name", "component_name", "test_name"],
    registry=registry,
)


def update_run_metrics(
    suite_name: str,
    component_name: str,
    run_duration: float,
    status: RunStatus,
) -> None:
    toolforge_test_run_status.labels(
        suite_name=suite_name,
        component_name=component_name,
    ).set(status.value)
    toolforge_test_run_duration.labels(
        suite_name=suite_name,
        component_name=component_name,
    ).set(run_duration)


def update_test_suite_metrics(
    suite_name: str,
    component_name: str,
    test_results: list[TestResult],
) -> None:
    for test_result in test_results:
        toolforge_test_run_test_status.labels(
            suite_name=suite_name, component_name=component_name, test_name=test_result.name
        ).set(test_result.status.value)

        if test_result.duration:
            toolforge_test_run_test_duration.labels(
                suite_name=suite_name, component_name=component_name, test_name=test_result.name
            ).set(test_result.duration)
