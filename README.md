# Routing Graph Packager HTTP API

![tests](https://github.com/gis-ops/kadas-routing-packager/workflows/tests/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/gis-ops/kadas-routing-packager/badge.svg?branch=master)](https://coveralls.io/github/gis-ops/kadas-routing-packager?branch=master)

A Flask app to schedule the generation of updated regional/local routing graph packages for open-source routing engines from a variety of data sources.

Supported routing engines:
- [Valhalla](https://github.com/valhalla/valhalla)
- [~~OSRM~~](https://github.com/Project-OSRM/osrm-backend) (coming soon..)
- [~~Graphhopper~~](https://github.com/graphhopper/graphhopper/) (coming soon..)
- [~~ORS~~](https://github.com/GIScience/openrouteservice) (coming soon..)

The default road dataset is [OSM](openstreetmap.org). If available, it also supports road datasets of commercial vendors, such as TomTom and HERE, assuming they are provided in the [OSM PBF format](https://wiki.openstreetmap.org/wiki/PBF_Format#).

For more details have a look at our [wiki](https://github.com/gis-ops/routing-graph-packager/wiki).

## Features

- **user store**: with basic authentication for `POST` and `DELETE` endpoints
- **bbox cuts**: generate routing packages within a bounding box
- **job scheduling**: schedule regular jobs, e.g. `daily`, `weekly` etc
- **asynchronous API**: graph generation is outsourced to a [`RQ`](https://github.com/rq/rq) worker
- **email notifications**: notifies the requesting user if the job succeeded/failed

For more details have a look at our [wiki](https://github.com/gis-ops/routing-graph-packager/wiki).

## "Quick Start"

**Note**, if you need/want to change any of the commands below (e.g. the OSM file), try the [Installation wiki](https://github.com/gis-ops/routing-graph-packager/wiki/Installation), which gives more detailed explanations.

First you need to clone the project and download an OSM file to its respective location:

```
git clone https://github.com/gis-ops/routing-graph-packager.git
cd routing-graph-packager && wget http://download.geofabrik.de/europe/andorra-latest.osm.pbf -O ./data/osm/andorra-latest.osm.pbf
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

With the project defaults, you can now make a `POST` request which will generate a graph package in `DATA_DIR` (default `./data`) from Andorra:

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
	"interval": "daily"  # the update interval, can be one of ["once", "daily", "weekly", "monthly"]
}'
```

After a minute you should have the graph package available in `./data/valhalla/valhalla_osm_test/`. If not, check the logs of the worker process or the Flask app.

The `routing-packager-worker` container has `cron` jobs running to update the routing packages in the root user's `crontab`.

The `routing-packager-app` container running the HTTP API has a `cron` job which runs daily updates of **all** OSM PBF files.

By default, also a fake SMTP server is started and you can see incoming messages on `http://localhost:1080`.

To set up regular updates for the registered graphs, see below.

For full configuration options, please consult our [wiki](https://github.com/gis-ops/routing-graph-packager/wiki/Configuration#complete-list).

## Concepts

### PBF files

Before starting the service, you need to supply at least one PBF file (e.g. from [Geofabrik](https://download.geofabrik.de)). To support multiple providers and keep the amount of manual configuration to a minimum, this project assumes a **rigid folder hierarchy** in its `DATA_DIR` (see [Configuration](https://github.com/gis-ops/routing-graph-packager/wiki/Configuration#complete-list), defaults to `./data`) where any PBF file is located in its provider directory, e.g.:

```
data
├── here
│   └── spain-latest.here.pbf
├── osm
│   └── andorra-latest.osm.pbf
└── tomtom
    └── switzerland-latest.tomtom.pbf
```

**Note**, you'll need **at least one PBF file** which covers all extents you ever want to generate graphs for (e.g. the full planet).

It's actually beneficial if you supply more and smaller files if possible. When generating a job the first time, we use `osmium extract` to produce a PBF extract. We try to be smart here: we find the optimal PBF to extract from by looking at each PBF's area. I.e. if you want a London `bbox` generated and you have e.g. `europe-latest.osm.pbf` and `england-latest.osm.pbf` in `./data/osm`, we'll choose the latter, so it'll be faster to extract. The smaller the input PBF is (and the smaller the `bbox` with which to extract), the faster `osmium` operates. The extracted PBF for each job is cached, so that subsequent jobs can use it as input PBF. So, if a later job would be only Camden Town, we'd extract that from the London job's extracted PBF.

All OSM PBFs will updated daily with the supplied `cron` script.

### Data sources

This service tries to be flexible in terms of data sources and routing engines. Consequently, we support proprietary dataset such as from TomTom or HERE.

However, all data sources **must be** in the OSM PBF format. We offer [commercial support](https://gis-ops.com/routing-and-optimisation/#data-services) in case of interest.

### `POST` new job

The app is listening on `/api/v1/jobs` for new `POST` requests to generate some graph according to the passed arguments. The lifecycle is as follows:

1. Request is parsed, inserted into the Postgres database and the new entry is immediately returned with a few job details as blank fields.
2. Before returning the response, the graph generation function is queued with `RQ` in a Redis database to dispatch to a worker.
3. If the worker is currently
    - **idle**, the queue will immediately start the graph generation:
        - Pull the job entry from the Postgres database
        - Update the job's `status` database field along the processing to indicate the current stage
		- If the current job has not been processed before:
        	- Cut an extract provided with `bbox` from the most optimal PBF file (the smallest one containing all of the job's `bbox`) with `osmium`
        - Start a docker container which generates the graph with the job's PBF file
        - Compress the files as `zip` or `tar.gz` and put them in `$DATA_DIR/<ROUTER>/<JOB_NAME>`, along with a metadata JSON
        - Clean up temporary files
    - **busy**, the current job will be put in the queue and will be processed once it reaches the queue's head
4. Send an email to the requesting user with success or failure notice (including the error message)

At this point you didn't set up regular graph updates yet. Refer to the [wiki Update Data section](https://github.com/gis-ops/routing-graph-packager/wiki/Data%20Updates) for that.
