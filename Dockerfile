#--- BEGIN Usual Python stuff ---
FROM python:3.10-slim-bullseye
LABEL maintainer=nils@gis-ops.com

# Install poetry
RUN apt-get update -y > /dev/null && \
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl > /dev/null && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python && \
    . $HOME/.poetry/env && \
    poetry config virtualenvs.create false && \
    poetry config virtualenvs.in-project true && \
    # remove before going live
    python -m venv .venv

#--- END Usual Python stuff ---

# Install docker, cron, osmctools & osmium
RUN apt-get update -y > /dev/null && \
    apt-get install -y --fix-missing \
        software-properties-common \
        gnupg \
        lsb-release \
        nano \
        jq \
        git \
        npm \
        cron -o APT::Immediate-Configure=0 > /dev/null && \
    # install docker & osmium
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get update -y > /dev/null && \
    apt-get install -y docker-ce docker-ce-cli containerd.io osmium-tool osmctools > /dev/null && \
    systemctl enable docker

WORKDIR /app

# Copy these first so no need to re-install only bcs source code changes
COPY pyproject.toml .
COPY poetry.lock .

# Install dependencies only
RUN . $HOME/.poetry/env && \
    python -m venv .venv && \
    . .venv/bin/activate && \
    poetry install --no-interaction --no-ansi --no-root --no-dev

# the current fork's branch doesn't have
RUN git clone https://github.com/python-restx/flask-restx && cd flask-restx && \
    pip install ".[dev]" && \
    restx_static="../.venv/lib/python3.10/site-packages/flask_restx/static" && \
    inv assets && \
    mkdir $restx_static && \
    ls -l ./node_modules/swagger-ui-dist && \
    /bin/bash -c "cp ./node_modules/swagger-ui-dist/{swagger-ui*.{css,js}{,.map},favicon*.png,oauth2-redirect.html} ${restx_static}" && \
    cp ./node_modules/typeface-droid-sans/index.css $restx_static/droid-sans.css && \
    cp -R ./node_modules/typeface-droid-sans/files $restx_static

COPY . .

# Install dependencies and remove unneeded stuff
RUN . $HOME/.poetry/env && \
    . .venv/bin/activate && \
    poetry install --no-interaction --no-ansi --no-dev && \
    mkdir -p /app/data

# add the root cert for https://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/, so osmupdate can download stuff
RUN mv /app/ssl/gwdg_root_cert.crt /usr/local/share/ca-certificates && \
    update-ca-certificates

EXPOSE 5000
HEALTHCHECK --start-period=5s CMD curl --fail -s http://localhost:5000/api/v1/jobs || exit 1

# Start gunicorn
ENTRYPOINT ["/bin/bash", "docker-entrypoint.sh"]
CMD ["app"]
