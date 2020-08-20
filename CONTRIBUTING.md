# Contribution Guidelines

## Submitting PRs

We :heart: patches & fixes and want to make sure everything goes smoothly for you while submitting a PR.

We use Google's [`yapf`](https://github.com/google/yapf) to make sure the formatting is consistent.

When contributing, we'd like you to:

- close an existing issue. If there is none yet for your fix, please [create one](https://github.com/gis-ops/routingpy/issues/new).
- write/adapt unit tests
- use docstrings for public classes/methods & responsible use of comments
- use meaningful commit messages
- you can branch off `master` and put a PR against `master` as well

## Setup

If you're planning to install/add new packages, we'd like you to use [`poetry`](https://python-poetry.org) as dependency/package manager instead of `pip`/`setuptools`.

1. Create and activate a new virtual environment

2. Install development dependencies:
    ```bash
    # From the root of your git project
    poetry install
    # or
    pip install -r requirements_dev.txt
    ```

3. Run tests to check if all goes well:
    ```bash
    pytest --cov=app
    ```

4. Please add a pre-commit hook for `yapf`, so your code gets auto-formatted before committing it:
    ```bash
    # From the root of your git project
    curl -o pre-commit.sh https://raw.githubusercontent.com/google/yapf/master/plugins/pre-commit.sh
    chmod a+x pre-commit.sh
    mv pre-commit.sh .git/hooks/pre-commit
    ```

## Tests

We use `pytest` in this project with `coverage`:

```bash
pytest --cov=app
``` 

A `coverage` bot will report the coverage in every PR and we might ask you to increase coverage on new code.
