#!/usr/bin/env bash

cmd=${1}

# either starts a worker or the app itself
if [ "${cmd}" == 'worker' ]; then
  /app/.venv/bin/rq worker packaging -u redis://redis:6379
elif [ "${cmd}" == 'app' ]; then
  /app/.venv/bin/gunicorn --config gunicorn.py http_app:app
else
  echo "Command ${cmd} not recognized. Choose from 'worker' or 'app'"
fi
