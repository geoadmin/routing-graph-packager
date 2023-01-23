#!/usr/bin/env bash

# Author: Nils Nolde <nils@gis-ops.com>
# Updated: 15-12-2022
# License: MIT
#
# Update OSM PBF files in batch by specifying a folder and a fixed update interval
#
# Put in cron, e.g.
# (crontab -l || true; echo "0 3 * * * /path/to/this/script.sh > /some_log.txt") | crontab -
#

# Change these addresses if applicable
export http_proxy=http://prxp01.admin.ch:8080
export https_proxy=http://prxp01.admin.ch:8080

usage()
{
    echo "usage: update_osm.sh --pbf/-p /app/data/osm/planet-latest.osm.pbf"
}

pbf=/app/data/osm/planet-latest.osm.pbf

# Get the arguments
while [ "$1" != "" ]; do
    case $1 in
        -p | --pbf )        shift
                                pbf=$1
                                ;;
        -h | --help )           usage
                                exit 0
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

echo "$(date "+%Y-%m-%d %H:%M:%S") Updating ${pbf} with the proxy settings: http_proxy: $http_proxy, https_proxy: $https_proxy"

fn=$(basename "${pbf}")
pbf_dir=$(dirname "$pbf")
pbf_name_updated="updated_${fn}"
pbf_updated="${pbf_dir}/${pbf_name_updated}"

# update the PBF
osmupdate --day "${pbf}" "${pbf_updated}"
mv "${pbf_updated}" "${pbf}"
