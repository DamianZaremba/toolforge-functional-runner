#!/bin/bash

# SSH key
if [ ! -z "${TOOLFORGE_FUNCTIONAL_TESTS_SSH_KEY}" ];
then
    echo "${TOOLFORGE_FUNCTIONAL_TESTS_SSH_KEY}" > /tmp/ssh-key
    chmod 600 /tmp/ssh-key
fi

# We don't have a passwd entry, ssh tries to resolve the uid, so let's fake one
echo "test-runner:x:$(id -u):$(id -g):Functional Test Runner:/workspace:/bin/bash" > /tmp/passwd
export NSS_WRAPPER_PASSWD=/tmp/passwd

echo "test-runner:x:$(id -g):myuser" > /tmp/group
export NSS_WRAPPER_GROUP=/tmp/group

export LD_PRELOAD=/layers/heroku_deb-packages/packages/usr/lib/x86_64-linux-gnu/libnss_wrapper.so

# Finally, run the actual logic
exec python -m toolforge_functional_runner.cli --ssh-key=/tmp/ssh-key --metrics-port=9091
