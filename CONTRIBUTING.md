# Contribution Guidelines

## Submitting PRs

We :heart: patches, fixes & feature PRs and want to make sure everything goes smoothly for you before and while while submitting a PR.

For development we use:
- [`poetry`](https://github.com/python-poetry/poetry/) as package manager
- `pytest` for testing
- Google's [`yapf`](https://github.com/google/yapf) to make sure the formatting is consistent.
- [`pre-commit`](https://pre-commit.com) hook for yapf

When contributing, ideally you:

- close an existing issue. If there is none yet for your fix, please [create one](https://github.com/gis-ops/routing-graph-packager/issues/new).
- write/adapt unit tests
- use docstrings for public classes/methods & responsible use of comments
- use meaningful commit messages
- branch off `master` and PR against `master` as well

## Setup

1. Create and activate a new virtual environment

2. Install development dependencies:
```bash
poetry install
```
   
3. Please add a pre-commit hook for `yapf`, so your code gets auto-formatted before committing it:
```bash
pre-commit install
```

## Tests

You'll need a few things to run the tests:

- PostreSQL installation with a DB named `gis_test` (or define another db name using `POSTGRES_DB_TEST`) **and PostGIS enabled**
- Redis database, best done with `docker run --name redis -p 6379:6379 -d redis:6.0`, then you can use the project's defaults, i.e. `REDIS_URL=redis://localhost:6379/0`
- some fake SMTP service to handle email tests, our recommendations:
    - [fake-smtp-server](https://www.npmjs.com/package/fake-smtp-server): NodeJS app with a frontend on `http://localhost:1080` and SMTP port 1025
    - pure Python one-liner in a separate terminal window: `sudo python -m smtpd -n -c DebuggingServer localhost:1025`

We use `pytest` in this project with `coverage`:

```bash
pytest --cov=routing_packager_app
``` 

A `coverage` bot will report the coverage in every PR and we might ask you to increase coverage on new code.
