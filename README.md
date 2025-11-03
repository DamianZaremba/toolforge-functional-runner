# Toolforge functional test runner

Helper script to execute the toolforge functional test suite in a continuous manner.

Expects a standard maintainer account with access to a standard tool account.

All tests/tooling are executed on the bastion host, as a normal user would.

### Execution

Example usage: `toolforge-functional-runner --ssh-key=~/.ssh/maintainer-ssh-key --single-run`

Metrics are accessible via `http://localhost:9515`, including suite/test status & duration.
