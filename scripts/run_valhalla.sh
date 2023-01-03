#!/usr/bin/env bash

# watch the .lock file every 10 secs
wait_for_lock() {
  count=0
  sleep=10
  max=3600
  while ! [[ $count == $max ]]; do
    if ! [[ -f $1 ]]; then
     return
    fi
    sleep $sleep
    count=$(( $count + $sleep ))
  done

  echo "max count reached"
  exit 1
}

PORT_8002="8002"
PORT_8003="8003"

CURRENT_PORT=""
CURRENT_VALHALLA_DIR=""
OLD_PORT=""
OLD_PID=""
iteration=0
while true; do
  (( iteration++ ))

  # Take 8002 if this is the first start
  if curl -fs "${IP}:${PORT_8002}/status"; then
    CURRENT_PORT=${PORT_8003}
    OLD_PORT=${PORT_8002}
    CURRENT_VALHALLA_DIR=$VALHALLA_DIR_8003
  elif curl -fs "${IP}:${PORT_8003}/status"; then
    CURRENT_PORT=${PORT_8002}
    OLD_PORT=${PORT_8003}
    CURRENT_VALHALLA_DIR=$VALHALLA_DIR_8002
  elif [[ $iteration != 0 ]]; then
    echo "ERROR: Neither localhost:8002 nor localhost:8003 is up."
    exit 1
  else
    CURRENT_PORT=${PORT_8002}
    CURRENT_VALHALLA_DIR=$VALHALLA_DIR_8002
  fi

  # wait until there's no .lock file anymore
  wait_for_lock "$CURRENT_VALHALLA_DIR"

  # build the current config
  valhalla_config="$CURRENT_VALHALLA_DIR/valhalla.json"
  valhalla_build_config \
    --httpd-service-listen "tcp://*:${CURRENT_PORT}" \
    --mjolnir-tile-extract "" \
    --mjolnir-tile-dir $CURRENT_VALHALLA_DIR \
    --mjolnir-concurrency "$CONCURRENCY" \
    > "${valhalla_config}" || exit 1

  # If it's the first one, check for the Valhalla dir and abort if it's there
  if [[ -z $OLD_PORT && $FORCE_BUILD == "False" ]]; then
    exec valhalla_service "$valhalla_config" 1 &
    OLD_PID=$!
    sleep 1
    continue;
  fi


  echo "INFO: Running build tiles with: ${valhalla_config} $DATA_DIR/planet-latest.osm.pbf"

  # if we should build with elevation we need to build the tiles in stages
  echo ""
  echo "============================"
  echo "= Build the initial graph. ="
  echo "============================"

  valhalla_build_tiles -c ${CONFIG_FILE} -e build ${files} || exit 1

  # Build the elevation data if requested
  if [[ $do_elevation == "True" ]]; then
    if [[ ${build_elevation} == "Force" ]] && ! test -d "${ELEVATION_PATH}"; then
      echo "WARNING: Rebuilding elevation tiles"
      rm -rf $ELEVATION_PATH || exit 1
    fi
    maybe_create_dir ${ELEVATION_PATH}
    echo ""
    echo "================================="
    echo "= Download the elevation tiles ="
    echo "================================="
    valhalla_build_elevation --from-tiles --decompress -c ${CONFIG_FILE} -v || exit 1
  fi

  echo ""
  echo "==============================="
  echo "= Enhancing the initial graph ="
  echo "==============================="
  valhalla_build_tiles -c ${CONFIG_FILE} -s enhance ${files} || exit 1

  echo "INFO: Successfully built files: ${files}"
  add_hashes "${files}"






done
