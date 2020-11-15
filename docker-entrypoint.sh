#!/usr/bin/env bash

cmd=${1}

# either starts a worker or the app itself
if [ "${cmd}" == 'worker' ]; then
  # also register the cron scripts
  cp /app/cron/routing_packager_daily.sh /etc/cron.daily/ && chmod +x /etc/cron.daily/routing_packager_daily.sh
  cp /app/cron/routing_packager_weekly.sh /etc/cron.weekly/ && chmod +x /etc/cron.weekly/routing_packager_weekly.sh
  cp /app/cron/routing_packager_monthly.sh /etc/cron.monthly/ && chmod +x /etc/cron.monthly/routing_packager_monthly.sh
  service cron start

  # Start the worker
  /app/.venv/bin/rq worker packaging -u redis://redis:6379
elif [ "${cmd}" == 'app' ]; then
  # The OSM updater script should run before; output cron to docker log
  # https://stackoverflow.com/a/16068840/2582935
  # TODO: support hourly/minutely, needs the implemenation in the app first
  cmd="/app/cron/routing_packager_update_osm.sh -i daily -b ${CLIP_BBOX} -p ${DATA_DIR}/${OSM_PBF}"
  (crontab -l || true; echo "0 3 * * * ${cmd} > /proc/1/fd/1 2>&1") | crontab -
  service cron start

  # Start the gunicorn server
  /app/.venv/bin/gunicorn --config gunicorn.py http_app:app
else
  echo "Command ${cmd} not recognized. Choose from 'worker' or 'app'"
fi
