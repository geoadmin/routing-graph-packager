# Routing Graph Packager HTTP API

![tests](https://github.com/gis-ops/kadas-routing-packager/workflows/tests/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/gis-ops/kadas-routing-packager/badge.svg?branch=master)](https://coveralls.io/github/gis-ops/kadas-routing-packager?branch=master)

A Flask app to schedule the generation of regional/local routing graph packages for open-source routing engines.

Supported routing engines:
- [Valhalla](https://github.com/valhalla/valhalla)
- [~~OSRM~~](https://github.com/Project-OSRM/osrm-backend) (coming soon..)
- [~~Graphhopper~~](https://github.com/graphhopper/graphhopper/) (coming soon..)
- [~~ORS~~](https://github.com/GIScience/openrouteservice) (coming soon..)

The default road dataset is [OSM](openstreetmap.org). If available, it also supports road datasets of commercial vendors, such as TomTom and HERE, assuming they are provided in the [OSM PBF format](https://wiki.openstreetmap.org/wiki/PBF_Format#).

The app **does not (yet) update the OSM data**. Consider using our [osm-data-updater](https://github.com/gis-ops/osm-data-updater) project for this job.

## Features

- **user store**: with basic authentication for `POST` and `DELETE` endpoints
- **bbox cuts**: generate routing packages within a bounding box
- **job scheduling**: schedule regular jobs, e.g. `daily`, `weekly` etc
- **asynchronous API**: graph generation is outsourced to a [`RQ`](https://github.com/rq/rq) worker
- **email notifications**: notifies the requesting user if the job succeeded/failed

For more details have a look at our [wiki](https://github.com/gis-ops/osm-data-updater/wiki).

## Quick Start

First you need to clone the project and download an OSM file:

```
git clone https://github.com/gis-ops/routing-graph-packager.git
cd routing-graph-packager && wget http://download.geofabrik.de/europe/andorra-latest.osm.pbf -O ./data/andorra-latest.osm.pbf
```

Since the graph generation takes place in docker containers, you'll also need the relevant images (depending on the routing engine you're interested in):

```
# Choose any or all of these images
docker pull gisops/valhalla:latest
docker pull osrm/osrm-backend:latest
docker pull graphhopper/graphhopper:latest
docker pull openrouteservice/openrouteservice:latest
```

The easiest way to quickly start the project is to use `docker-compose`:

```
docker-compose up -d
```

With the project defaults, you can now make a `POST` request which will generate a graph package in `DATA_DIR`:

```
curl --location -XPOST 'http://localhost:5000/api/v1/jobs' \
--header 'Authorization: Basic YWRtaW5AZXhhbXBsZS5vcmc6YWRtaW4=' \
--header 'Content-Type: application/json' \
--data-raw '{
	"name": "test",  # name needs to be unique for a specific router & provider
	"description": "test descr",  
	"bbox": "1.531906,42.559908,1.6325,42.577608",  # the bbox as minx,miny,maxx,maxy
	"provider": "osm",  # the dataset provider, needs to be registered in ENABLED_PROVIDERS
	"router": "valhalla",  # the routing engine, needs to be registered in ENABLED_ROUTERS and the docker image has to be available
    "compression": "tar.gz",  # the compression method, can be "tar.gz" or "zip"
    "interval": "daily"  # the update interval, can be one of ["once", "daily", "weekly", "monthly", "yearly"]
}'
```

After a minute you should have the graph package available in `./data/valhalla/valhalla_osm_test/`. If not, check the logs of the worker process or the Flask app.

The `routing-packager-worker` container has `cron` jobs running to update the routing packages in `/etc/cron.[daily,weekly,monthly]`.

By default, also a fake SMTP server is started and you can see incoming messages on `http://localhost:1080`.

For full configuration options, please consult our [wiki](https://github.com/gis-ops/osm-data-updater/wiki).

## Concepts

### General

The app is listening on `/api/v1/jobs` for new `POST` requests to generate some graph according to the passed arguments. The lifecycle is as follows:

1. Request is parsed, inserted into the Postgres database and the new entry is immediately returned with all job details as blank fields.
2. Before returning the response, the graph generation function is queued with `RQ` in a Redis database to dispatch to a worker.
3. If the worker is currently
    - **idle**, the queue will immediately start the graph generation:
        - Pull the job entry from the Postgres database
        - Update the job's `status` database field along the processing to indicate the current stage 
        - Cut an extract provided with `bbox` from the configured PBF with `osmium`
        - Start a docker container which generates the graph with the extracted PBF file
        - Compress the files as `zip` or `tar.gz` and put them in `$DATA_DIR/<ROUTER>/<JOB_NAME>`, along with a metadata JSON
        - Clean up temporary files
    - **busy**, the current job will be put in the queue and will be processed once it reaches the queue's head
4. Send an email to the requesting user with success or failure notice (including the error message)

### Recurring graph generations

The app is capable of running scheduled updates on registered graph generation jobs. The update frequency is determined by the job entry's `interval` field. Valid values for `interval` are ["once", "daily", "weekly", "monthly", "yearly"], while "once" is never updated.

The app provides a command line interface (`flask update`) to automate the updates:

```
$PWD/.venv/bin/flask update --help 
Usage: flask update [OPTIONS] INTERVAL

  Update routing packages according to INTERVALs, one of ['once', 'daily',
  'weekly', 'monthly', 'yearly'].

Options:
  -c, --config [development|production|testing]
                                  Internal option
  --help                          Show this message and exit.
```

The script will pull the job entries with matching `INTERVAL` and let the worker spin up the update procedures one-by-one. 

You can find the appropriate scripts in the `./cron` directory. Inside the scripts change the location of the `flask` executable according to your setup and copy them to the respective `cron` folders:

```
sudo cp ./cron/routing_packager_daily.sh /etc/cron.daily
sudo cp ./cron/routing_packager_weekly.sh /etc/cron.weekly
sudo cp ./cron/routing_packager_monthly.sh /etc/cron.monthly
```

Of course you can also use `crontab` to manage the jobs with more scheduling granularity.
