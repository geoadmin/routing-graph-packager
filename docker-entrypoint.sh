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
  # TODO: support hourly/minutely, needs the implementation in the app first
  register_cron_script "0 3 * * *" "/app/cron/routing_packager_update_osm.sh -i daily -d /app/data/osm"
  service cron start

  # Start the gunicorn server
  /app/.venv/bin/gunicorn --config gunicorn.py http_app:app
else
  echo "Command ${cmd} not recognized. Choose from 'worker' or 'app'"
fi
