#!/usr/bin/env bash

usage()
{
    echo "usage: routing_packager_update_osm.sh --interval -i [minutely|hourly|daily|weekly] --bbox -b minx,miny,maxx,maxy --pbf -p your-file.osm.pbf"
}

interval=daily
bbox="1.531906,42.559908,1.6325,42.577608"
pbf=/app/data/andorra-latest.osm.pbf

# Get the arguments
while [ "$1" != "" ]; do
    case $1 in
        -i | --interval )       shift
                                interval=$1
                                ;;
        -b | --bbox )           shift
                                bbox=$1
                                ;;
        -p | --pbf )            shift
                                pbf=$1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

# Validate at least the interval
if ! [[ "$interval" =~ ^(minutely|hourly|daily|weekly)$ ]]; then
  echo "argument --interval '${interval}' is not a valid option."
  usage
  exit 1
fi

opts=""
if [[ $interval == 'hourly' ]]; then
  opts+='--hour --day'
elif [[ $interval =~ ^(daily|weekly)$ ]]; then
  opts+='--day'
fi

pbf_dir=`dirname "${pbf}"`
pbf_name=`basename "${pbf}"`
pbf_name_updated="updated_${pbf_name}"
pbf_updated="${pbf_dir}/${pbf_name_updated}"
osmupdate -v ${opts} -b=${bbox} ${pbf} ${pbf_updated} || exit 1

# overwrite the previous file
mv ${pbf_updated} ${pbf}
