#!/usr/bin/env bash

cmd=${1}

# either starts a worker or the app itself
if [ "${cmd}" == 'worker' ]; then
  # Start the worker
  /app/.venv/bin/rq worker packaging -u redis://redis:6379
elif [ "${cmd}" == 'app' ]; then
  # SSL? Provided by .docker_env with path mapped in docker-compose.yml
  opts=''
  if [ -n "${SSL_CERT}" ] && [ -n "${SSL_KEY}" ]; then
    opts="--certfile ${SSL_CERT} --keyfile ${SSL_KEY}"
    echo "Provided SSL certificate ${SSL_CERT} with SSL key ${SSL_KEY}."
  else
    echo "No SSL configured."
  fi

  # Start the gunicorn server
  bash -c "/app/.venv/bin/gunicorn --config gunicorn.py ${opts} http_app:app"
else
  echo "Command ${cmd} not recognized. Choose from 'worker' or 'app'"
fi
