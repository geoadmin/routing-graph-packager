#--- BEGIN Usual Python stuff ---
FROM python:3.10-slim-bullseye
LABEL maintainer=nils@gis-ops.com

WORKDIR /app
ENV POETRY_BIN $HOME/.local/share/pypoetry/venv/bin/poetry

# Install vis
RUN apt-get update -y > /dev/null && \
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl > /dev/null && \
    pip install --upgrade pip

RUN curl -sSL https://install.python-poetry.org | python && \
    $POETRY_BIN config virtualenvs.create false && \
    $POETRY_BIN config virtualenvs.in-project true && \
    # remove before going live
    python -m venv .venv

#--- END Usual Python stuff ---

# TODO: only install pyosmium to update the planet
RUN apt-get update -y > /dev/null && \
    apt-get install -y osmium-tool osmctools > /dev/null

# Copy these first so no need to re-install only bcs source code changes
COPY pyproject.toml .
COPY poetry.lock .

# Install dependencies.py only
RUN . .venv/bin/activate && \
    $POETRY_BIN install --no-interaction --no-ansi --no-root --only main

COPY . .

# Install dependencies.py and remove unneeded stuff
RUN . .venv/bin/activate && \
    $POETRY_BIN install --no-interaction --no-ansi --only main && \
    mkdir -p /app/data

# add the root cert for https://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/, so osmupdate can download stuff
RUN mv /app/ssl/gwdg_root_cert.crt /usr/local/share/ca-certificates && \
    update-ca-certificates

EXPOSE 5000
HEALTHCHECK --start-period=5s CMD curl --fail -s http://localhost:5000/api/v1/jobs || exit 1

# Start gunicorn
ENTRYPOINT ["/bin/bash", "docker-entrypoint.sh"]
CMD ["app"]
