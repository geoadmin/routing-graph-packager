#!/usr/bin/env bash

# Author: Nils Nolde <nils@gis-ops.com>
# Updated: 15-12-2022
# License: MIT
#
# Rotationally build Valhalla tiles to 2 different directories (env vars from docker-compose.yml).
# Respects a .lock file and waits for it to disappear before nuking the tileset.
#
# Note, that some variables here are sourced from the .env/.docker_env file.
#
# Usage: ./run_valhalla.sh
#

# so it can see prime_server within the supervisor process
export LD_LIBRARY_PATH=/usr/local/lib

# watch the .lock file every 10 secs
wait_for_lock() {
  count=0
  sleep=10
  max=3600
  while ! [[ $count == $max ]]; do
    if ! [[ -f $1/.lock ]]; then
     return
    fi
    echo "INFO: sleeping for $sleep seconds to wait for .lock file to disappear at $1"
    sleep $sleep
    count=$(( $count + $sleep ))
  done

  echo "ERROR: max count reached"
  exit 1
}

reset_config() {
  jq --arg d "" '.mjolnir.tile_dir = $d' "${valhalla_config}"| sponge "${valhalla_config}"
}

PORT_8002="8002"
PORT_8003="8003"
# $DATA_DIR needs to be defined, either by supervisor or the current shell
VALHALLA_DIR_8002="$DATA_DIR/osm/$PORT_8002"
VALHALLA_DIR_8003="$DATA_DIR/osm/$PORT_8003"
# TODO: change PBF
PBF="/app/data/osm/brandenburg-latest.osm.pbf"

CURRENT_PORT=""
CURRENT_VALHALLA_DIR=""
OLD_PORT=""
OLD_PID=""
iteration=0
while true; do
  (( iteration++ ))

  echo "INFO: Starting iteration $iteration..."

  # Take 8002 if this is the first start
  if curl -fs "http://localhost:${PORT_8002}/status"; then
    CURRENT_PORT=${PORT_8003}
    OLD_PORT=${PORT_8002}
    CURRENT_VALHALLA_DIR=$VALHALLA_DIR_8003
  elif curl -fs "http://localhost:${PORT_8003}/status"; then
    CURRENT_PORT=${PORT_8002}
    OLD_PORT=${PORT_8003}
    CURRENT_VALHALLA_DIR=$VALHALLA_DIR_8002
  elif [[ $iteration != 1 ]]; then
    echo "ERROR: Neither localhost:8002 nor localhost:8003 is up."
    exit 1
  else
    CURRENT_PORT=${PORT_8002}
    CURRENT_VALHALLA_DIR=$VALHALLA_DIR_8002
  fi

  if ! [[ -d $CURRENT_VALHALLA_DIR ]]; then
    mkdir -p $CURRENT_VALHALLA_DIR
  fi

  # download the PBF file if need be
  # TODO: change PBF URL
  UPDATE_OSM="True"
  if ! [ -f "$PBF" ]; then
    echo "INFO: Downloading OSM file $PBF"
    # wget -nv https://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/pbf/planet-latest.osm.pbf -O "$PBF" || exit 1
    wget -nv https://download.geofabrik.de/europe/germany/brandenburg-latest.osm.pbf -O "$PBF" || exit 1
    UPDATE_OSM="False"
  fi

  if [[ $UPDATE_OSM == "True" ]]; then
    echo "INFO: Updating OSM file $PBF"
    update_osm.sh -p "$PBF" || exit 1
  fi

  # build the current config
  echo "INFO: Building valhalla.json to $CURRENT_VALHALLA_DIR"
  valhalla_config="$CURRENT_VALHALLA_DIR/valhalla.json"
  valhalla_build_config \
    --httpd-service-listen "tcp://*:${CURRENT_PORT}" \
    --mjolnir-tile-extract "" \
    --mjolnir-tile-dir "$CURRENT_VALHALLA_DIR" \
    --mjolnir-concurrency "$CONCURRENCY" \
    > "${valhalla_config}" || exit 1

  # wait until there's no .lock file anymore
  wait_for_lock "$CURRENT_VALHALLA_DIR"

  # If it's the first start and a graph already exists, continue with next build
  if [[ -z $OLD_PORT && -d $CURRENT_VALHALLA_DIR ]]; then
    # remove the reference to tiles_dir so the service doesn't actually load the tiles
    reset_config
    exec valhalla_service "$valhalla_config" 1 &
    OLD_PID=$!
    echo "INFO: Started Valhalla the first time with config $valhalla_config on with PID $OLD_PID"
    sleep 1
    echo ""
    echo ""
    continue
  fi

  echo "INFO: Running build tiles with: $PBF"
  valhalla_build_tiles -c "${valhalla_config}" "$PBF" || exit 1
  reset_config

  # shut down the old service and launch the new one
  echo "INFO: Killing Valhalla on port $OLD_PORT with PID $OLD_PID"
  kill -9 $OLD_PID
  exec valhalla_service "$valhalla_config" 1 &
  OLD_PID=$!
  echo "INFO: Started Valhalla on port $CURRENT_PORT with PID $OLD_PID"

  sleep 120
  echo ""
  echo ""

done
