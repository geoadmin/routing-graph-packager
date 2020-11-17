#--- BEGIN Usual Python stuff ---
FROM python:3.8-slim-buster
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
    apt-get install -y \
        software-properties-common \
        gnupg-agent \
        nano \
        cron -o APT::Immediate-Configure=0 > /dev/null && \
    # install docker
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get update -y > /dev/null && \
    apt-get install -y docker-ce docker-ce-cli containerd.io > /dev/null && \
    systemctl enable docker && \
    # install osmium
    add-apt-repository 'deb http://ftp.debian.org/debian sid main' && \
    apt-get update -y > /dev/null && \
    apt-get install -y osmium-tool osmctools > /dev/null

WORKDIR /app

COPY . .

# Install dependencies and remove unneeded stuff
RUN . $HOME/.poetry/env && \
    python -m venv .venv && \
    . .venv/bin/activate && \
    poetry install --no-interaction --no-ansi && \
    mkdir -p /app/data && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 5000
HEALTHCHECK --start-period=5s CMD curl --fail -s http://localhost:5000/api/v1/jobs || exit 1

# Start gunicorn
ENTRYPOINT ["/bin/bash", "docker-entrypoint.sh"]
CMD ["app"]
