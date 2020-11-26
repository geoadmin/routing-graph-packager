#!/usr/bin/env bash

usage()
{
    echo "usage: routing_packager_update_osm.sh --interval/-i [minutely|hourly|*daily*|weekly] --dir-pbf/-d /app/data/osm"
}

interval=daily
pbf_dir=/app/data/osm

# Get the arguments
while [ "$1" != "" ]; do
    case $1 in
        -i | --interval )       shift
                                interval=$1
                                ;;
        -d | --dir-pbf )        shift
                                pbf_dir=$1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

# Validate the interval
if ! [[ "$interval" =~ ^(minutely|hourly|daily|weekly)$ ]]; then
  echo "argument --interval '${interval}' is not a valid option."
  usage
  exit 1
fi

# Validate if there's PBF files
pbf_expansion="${pbf_dir}/*.pbf"
pbf_count=$(ls $pbf_expansion | wc -l)
if [[ $pbf_count == 0 ]]; then
  echo "No PBF files in ${pbf_dir}."
  exit 1
fi

opts=""
if [[ $interval == 'hourly' ]]; then
  opts+='--hour --day'
elif [[ $interval =~ ^(daily|weekly)$ ]]; then
  opts+='--day'
fi

echo "$(date "+%Y-%m-%d %H:%M:%S") Updating PBFs in ${pbf_dir}"

counter=0
for f in $pbf_expansion
do
  fn=$(basename "${f}")
  pbf_name_updated="updated_${fn}"
  pbf_updated="${pbf_dir}/${pbf_name_updated}"

  # Extract the bbox with osmium
  bbox=$(osmium fileinfo -j ${f} | jq .header.boxes[0])
  # Warn if bbox is not populated in PBF and continue with next
  # Otherwise osmupdate would pull ALL planet changes into this PBF
  [[ -z "$bbox" ]] && echo "bbox of ${f} is empty" && continue
  # Sanitize the bbox string
  bbox_sanitized=${bbox//[$'\t\r\n ']}

  # Only keep the temp files if it's not the last PBF
  (( counter++ ))
  if [[ $counter != "${pbf_count}" ]]; then
    update_cmd=$(osmupdate --keep-tempfiles ${opts} -b="${bbox_sanitized:1:-1}" "${f}" "${pbf_updated}")
    # exit if the last command failed
    if ! $update_cmd; then
      echo "Couldn't update OSM file ${fn} with command ${update_cmd}."
      continue
    fi
  else
    update_cmd=$(osmupdate ${opts} -b="${bbox_sanitized:1:-1}" "${f}" "${pbf_updated}")
    if ! $update_cmd; then
      echo "Couldn't update OSM file ${fn} with command ${update_cmd}."
      continue
    fi
    # just in case osmupdate didn't delete the fairly big osmupdate_temp folder
    [[ -d osmupdate_temp ]] && rm -r osmupdate_temp || true
  fi

  # finally overwrite the previous file
  mv "${pbf_updated}" "${f}"
done
