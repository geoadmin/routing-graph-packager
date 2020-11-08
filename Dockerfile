#--- BEGIN Usual Python stuff ---
FROM python:3.8-slim-buster
MAINTAINER Nils Nolde <nils@openrouteservice.org>

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
    python -m venv .venv

#--- END Usual Python stuff ---

# Install docker
RUN apt-get update -y > /dev/null && \
    apt-get install -y \
        gnupg-agent \
        software-properties-common > /dev/null && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get update -y > /dev/null && \
    apt-get install -y docker-ce docker-ce-cli containerd.io > /dev/null && \
    systemctl enable docker

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN . $HOME/.poetry/env && \
    . .venv/bin/activate && \
    poetry install --no-interaction --no-ansi && \
    rm -rf /var/lib/apt/lists/*
COPY config.py .
COPY kadas_routing_http ./app/
COPY http_app.py .

RUN mkdir -p /app/data

EXPOSE 5000

# Start gunicorn
ENTRYPOINT ["gunicorn", "--config", "gunicorn.py", "http_app:app"]