#!/usr/bin/env bash

# Run the script and pipe stdout/stderr to Docker's log
# On host this equals /dev/null, so rather pipe somewhere else
/app/.venv/bin/flask update monthly > /proc/1/fd/1 2>&1 || exit 1
