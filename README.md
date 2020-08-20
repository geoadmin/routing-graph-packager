# Routing Packager HTTP API

![tests](https://github.com/gis-ops/kadas-routing-packager/workflows/Tests/badge.svg)
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

### Quick Start

To quickly run the flask app, just type

```
flask run
```

The server will listen at `http://localhost:5000`

### Configuration

Most of the configuration takes place over environment variables. Flask supports `.env` files. For an overview over environment variables and their meaning, see the following table:

| Variable            | Required                      | Description                                                                                                             |
|---------------------|-------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| `FLASK_ENV`         | :negative_squared_cross_mark: | Determines the Flask environment, see the [official documentation](https://flask.palletsprojects.com/en/1.1.x/config/). |
| `FLASK_CONFIG`      | :ballot_box_with_check:       | Controls the app-specific environment, one of production, development, testing.                                         |
| `SQLITE_URL`        | :negative_squared_cross_mark: | The URL for the SQLite database, e.g. `sqlite:////home/user/db.db`. Default: `./app.db`                                 |
| `DB_ADMIN_EMAIL`    | :negative_squared_cross_mark: | The email address of the admin user. Acts as user name. Default: admin@example.org.                                     |
| `DB_ADMIN_PASSWORD` | :negative_squared_cross_mark: | The password of the admin user. Default: admin.                                                                         |
| `SECRET_KEY`        | :negative_squared_cross_mark: | The Flask secret. Even though there's a default, it's **strongly recommended** to change this.                              |


## Usage
