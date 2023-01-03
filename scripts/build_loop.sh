#!/usr/bin/env bash

OSM_FILE=$1
DATA_DIR="/opt/valhalla"
CONFIG_FILE="${DATA_DIR}/valhalla.json"
TILE_DIR="${DATA_DIR}/valhalla_tiles"
ADMIN_FILE="${DATA_DIR}/admins.sqlite"
TZ_FILE="${DATA_DIR}/timezones.sqlite"
ELEV_DIR="${DATA_DIR}/elevation"
BUILDER_TAR="${DATA_DIR}/valhalla_tiles.tar"

IP="162.55.2.221"
PORT_1="8000"
PORT_2="8001"

TODAY=$(date +"%Y-%m-%d")

email() {
      echo $1 | mail -s "Valhalla FOSSGIS Builder" info@gis-ops.com
      exit 1
}

# loop over both servers forever
err="Unknown error. Check the supervisor logs."
while true; do
      # some sanity checks
      if ! [[ -f ${OSM_FILE} ]]; then
            err="OSM file not found: ${OSM_FILE}"
            break
      fi
      if ! command -v valhalla_build_config; then
            err="Valhalla is not yet installed"
            break
      fi

      # Find out which Valhalla server is currently live
      # no need to protect for both servers being down
      # TODO: why not?
      if curl -fs "${IP}:${PORT_1}/status"; then
            CURRENT_PORT=${PORT_2}
            OLD_PORT=${PORT_1}
      else
            CURRENT_PORT=${PORT_1}
            OLD_PORT=${PORT_2}
      fi
      RUNNER_GZ="${DATA_DIR}/valhalla_tiles_${CURRENT_PORT}.tar.gz"

      echo "${TODAY} Starting to build tiles for instance ${CURRENT_PORT}"

      # Create the config (or overwrite)
      valhalla_build_config \
            --mjolnir-tile-dir ${TILE_DIR} \
            --mjolnir-tile-extract ${BUILDER_TAR} \
            --mjolnir-admin ${ADMIN_FILE}\
            --mjolnir-timezone ${TZ_FILE} \
            --mjolnir-traffic-extract "" \
            --mjolnir-transit-dir "" \
            --additional-data-elevation ${ELEV_DIR} \


      # Build the databases, if necessary
      if ! [[ -f ${ADMIN_FILE} ]]; then
            valhalla_build_admins -c ${CONFIG_FILE} ${OSM_FILE} || break
      fi

      if ! [[ -f ${TZ_FILE} ]]; then
            valhalla_build_timezones > ${TZ_FILE} || break
      fi

      echo "${TODAY} Starting to build tiles for instance ${CURRENT_PORT}"

      # then build the tiles in stages so we can download only the elevation tiles the graph needs
      # downside: no elevation for water areas (except along ferry routes)
      valhalla_build_tiles -c ${CONFIG_FILE} -e build ${OSM_FILE} || break

      if ! [[ -d ${ELEV_DIR} ]]; then
            valhalla_build_elevation -c ${CONFIG_FILE} --from-tiles --parallelism $(nproc) --decompress || break
      fi

      valhalla_build_tiles -c ${CONFIG_FILE} -s enhance ${OSM_FILE} || break

      # tar the tiles and send them to the runner
      valhalla_build_extract -c ${CONFIG_FILE} -v || break

      echo "${TODAY} Finished building tiles for instance ${CURRENT_PORT}\n"

      # compress the tar
      gzip -qf ${BUILDER_TAR}

      scp "${BUILDER_TAR}.gz" valhalla_service:${RUNNER_GZ}
      if ! [[ $? == 0 ]]; then
            err="Couldn't scp ${BUILDER_TAR} to valhalla_service:${RUNNER_GZ}"
            break
      fi

      # now decompress the tar, turn off supervisord for old config and turn on with new config
      ssh valhalla_service "gzip -fd ${RUNNER_GZ} && sudo supervisorctl start service${CURRENT_PORT}: && sudo supervisorctl stop service${OLD_PORT}:"
      if ! [[ $? == 0 ]]; then
            err="Failed to switch Valhalla instances for OLD = ${OLD_PORT}, NEW = ${CURRENT_PORT}."
            break
      fi

      # test if the new setup works as expected
      if ! curl -fs "${IP}:${CURRENT_PORT}/status"; then
            err="Switched to new instance ${CURRENT_PORT}, but can't get a successful request."
            break
      fi
      echo "${TODAY} Successful build finished for ${CURRENT_PORT}."

      # update OSM from the daily mirror
      pyosmium-up-to-date -v --server https://planet.osm.org/replication/day --size 4000 $OSM_FILE
      if ! [[ $? == 0 ]]; then
            err="${TODAY} Couldn't update OSM"
            break
      fi
done

email "${err}"

