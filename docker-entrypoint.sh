#!/usr/bin/env bash

register_cron_script () {
  # https://stackoverflow.com/a/16068840/2582935
  # Registers a job with crontab on root and pipe stdout/stderr to docker logs
  (crontab -l || true; echo "${1} ${2} > /proc/1/fd/1 2>&1") | crontab -
}

cmd=${1}

# either starts a worker or the app itself
if [ "${cmd}" == 'worker' ]; then
  # register the cron scripts
  register_cron_script "0 6 * * *" "/app/cron/routing_packager_daily.sh"
  register_cron_script "0 7 * * 7" "/app/cron/routing_packager_weekly.sh"
  register_cron_script "0 8 1 * *" "/app/cron/routing_packager_monthly.sh"
  service cron start

  # Start the worker
  /app/.venv/bin/rq worker packaging -u redis://redis:6379
elif [ "${cmd}" == 'app' ]; then
  # Create the script first which can be sourced from the cron job itself
  # otherwise there's not the right env vars set in the cron job's script
  echo -e "http_proxy=$http_proxy\nhttps_proxy=$https_proxy" > /app/cron/cron_env.sh
  chmod +x /app/cron/cron_env.sh
  # TODO: support hourly/minutely, needs the implementation in the app first
  register_cron_script "0 3 * * *" "BASH_ENV=/app/scripts/cron_env.sh /app/cron/routing_packager_update_osm.sh -i daily -d /app/data/osm"
  service cron start

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
