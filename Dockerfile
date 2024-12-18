#--- BEGIN Usual Python stuff ---

FROM ghcr.io/valhalla/valhalla:latest AS builder
LABEL maintainer="Nils Nolde <nils@gis-ops.com>"

WORKDIR /app

# Install vis
RUN apt-get update -y > /dev/null && \
    apt-get install -y \
    apt-transport-https \
    ca-certificates \
    python-is-python3 \
    python3-pip \
    python3-venv \
    curl > /dev/null

ENV POETRY_BIN=/root/.local/bin/poetry

RUN curl -sSL https://install.python-poetry.org | python && \
    $POETRY_BIN config virtualenvs.create false && \
    $POETRY_BIN config virtualenvs.in-project true && \
    python -m venv app_venv

# Copy these first so no need to re-install only bcs source code changes
COPY pyproject.toml .
COPY poetry.lock .

# Install dependencies.py only
RUN . app_venv/bin/activate && \
    $POETRY_BIN install --no-interaction --no-ansi --no-root --only main

COPY . .

# Install dependencies.py and remove unneeded stuff
RUN . app_venv/bin/activate && \
    $POETRY_BIN install --no-interaction --no-ansi --only main && \
    mkdir -p /app/data

# Do some Valhalla stuff

# remove some stuff from the original image
RUN cd /usr/local/bin && \
    preserve="valhalla_service valhalla_build_tiles valhalla_build_config valhalla_build_admins valhalla_build_timezones valhalla_build_elevation valhalla_ways_to_edges valhalla_build_extract valhalla_export_edges valhalla_add_predicted_traffic" && \
    mv $preserve .. && \
    for f in valhalla*; do rm $f; done && \
    cd .. && mv $preserve ./bin

FROM ubuntu:24.04 AS runner_base
LABEL maintainer="Nils Nolde <nils@gis-ops.com>"

# install Valhalla stuff
RUN apt-get update > /dev/null && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y libluajit-5.1-dev \
    libzmq5 libgdal-dev libczmq4 spatialite-bin libprotobuf-lite32 sudo locales wget \
    libsqlite3-0 libsqlite3-mod-spatialite libcurl4 python-is-python3 osmctools \
    python3.12-minimal curl unzip moreutils jq spatialite-bin supervisor > /dev/null

WORKDIR /app

ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"
# export the True defaults
ENV use_tiles_ignore_pbf=True
ENV build_tar=True
ENV serve_tiles=True

COPY . .

COPY --from=builder /usr/local /usr/local
COPY --from=builder /app/app_venv /app/app_venv
COPY --from=builder /app/scripts/* /usr/local/bin/
COPY --from=builder /app/conf/* /etc/supervisor/conf.d/

# add the root cert for https://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/, so osmupdate can download stuff
RUN mv /app/ssl/gwdg_root_cert.crt /usr/local/share/ca-certificates && \
    update-ca-certificates

EXPOSE 5000
HEALTHCHECK --start-period=5s CMD curl --fail -s http://localhost:5000/api/v1/jobs || exit 1

# Start gunicorn
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["app"]
