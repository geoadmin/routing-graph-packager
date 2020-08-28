# Routing Packager HTTP API

![tests](https://github.com/gis-ops/kadas-routing-packager/workflows/tests/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/gis-ops/kadas-routing-packager/badge.svg?branch=master)](https://coveralls.io/github/gis-ops/kadas-routing-packager?branch=master)

**This project is in development, more updates follow soon.**

## Installation

In this project we intentionally don't offer the classic `setuptools` installation and instead rely on [`poetry`](https://python-poetry.org) as package and dependency manager:

```bash
python -m venv .venv
poetry install [--no-dev]
```

Of course, just `pip` works too:

```bash
python -m venv .venv
pip install -r requirements.txt
```

### Requirements

- Python >= 3.7
- `osmium`
- PostgreSQL database with PostGIS enabled


### Quick Start

To quickly run the flask app, just type

```
flask run
```

The server will listen at `http://localhost:5000`

### Configuration

Most of the configuration takes place over environment variables. Flask supports `.env` files in the root directory. The PostgreSQL related variables are named the same as in Kartoza's excellent [PostGIS image](https://github.com/kartoza/docker-postgis).

For an overview over environment variables and their meaning, see the following table:

| Variable            | Type | Description                                                                                                                       |
|---------------------|------|-----------------------------------------------------------------------------------------------------------------------------------|
| `FLASK_ENV`         | str  | Determines the Flask environment, see the [official documentation](https://flask.palletsprojects.com/en/1.1.x/config/).           |
| `SECRET_KEY`        | str  | The Flask secret. Even though there's a default, it's **strongly recommended to change this**.                                        |
| `FLASK_CONFIG`      | str  | Controls the app-specific environment, one of `production`, `development`, `testing`. Default `production`.                             |
| `DB_ADMIN_EMAIL`    | str  | The email address of the admin user. Acts as user name. Default admin@example.org.                                               |
| `DB_ADMIN_PASSWORD` | str  | The password of the admin user. Default `admin`.                                                                                   |
| `POSTGRES_HOST`     | str  | The host of your PostgreSQL installation, e.g. IP or `postgis.example.org`. Default `localhost`.                                  |
| `POSTGRES_PORT`     | int  | The port of your PostgreSQL installation. Default 5432.                                                                           |
| `POSTGRES_DB`       | str  | The name of the **existing** database to use. Default `gis`.                                                                      |
| `POSTGRES_USER`     | str  | The admin user of the **existing** database. Default `admin`.                                                                     |
| `POSTGRES_PASS`     | str  | The admin password of the **existing** database. Default `admin`.                                                                 |
| `SMTP_HOST`         | str  | The host name for the SMTP server, e.g. `smtp.gmail.com`. Default `localhost`.                                                    |
| `SMTP_PORT`         | int  | The port for the SMTP server Default 587.                                                                                         |
| `SMTP_USER`         | str  | The user name for the email account. If omitted, no authentication will be attempted.                                             |
| `SMTP_PASS`         | str  | The password for the email account. If omitted, no authentication will be attempted.                                              |
| `SMTP_SECURE`       | bool | Whether TLS should be used to secure the email communication, `True` or `False` Default `False`.                                  |
| `ENABLED_PROVIDERS` | str  | The data providers to enable as a comma-delimited string, e.g. `osm,tomtom,here`. Default `osm`.                                  |
| `ENABLED_ROUTERS`   | str  | The routing engines to enable as a comma-delimited string, e.g. `valhalla,openrouteservice,osrm,graphhopper`. Default `valhalla`. |
| `VALHALLA_IMAGE`    | str  | The Valhalla Docker image to use in the tile generation. Default `gisops/valhalla:3.0.9`.                                         |                                                                       |

## Usage
