#!/usr/bin/env bash

cmd=${1}

# either starts a worker or the app itself
if [ "${cmd}" == 'worker' ]; then
  # also register the cron scripts
  cp /app/cron/routing_packager_daily.sh /etc/cron.daily/ && chmod +x /etc/cron.daily/routing_packager_daily.sh
  cp /app/cron/routing_packager_weekly.sh /etc/cron.weekly/ && chmod +x /etc/cron.daily/routing_packager_weekly.sh
  cp /app/cron/routing_packager_monthly.sh /etc/cron.monthly/ && chmod +x /etc/cron.daily/routing_packager_monthly.sh
  service cron start

  /app/.venv/bin/rq worker packaging -u redis://redis:6379
elif [ "${cmd}" == 'app' ]; then
  /app/.venv/bin/gunicorn --config gunicorn.py http_app:app
else
  echo "Command ${cmd} not recognized. Choose from 'worker' or 'app'"
fi
