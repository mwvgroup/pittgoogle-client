# Manage dependencies with Poetry

This page contains instructions for managing the `pittgoogle-client` package dependencies using [Poetry](https://python-poetry.org/).
Poetry was implemented in this repo in [pull #7](https://github.com/mwvgroup/pittgoogle-client/pull/7).

## Setup your environment

Create a new conda environment for poetry and install it ([Poetry installation](https://python-poetry.org/docs/#installation)).
If you already did this, just activate the environment.

```bash
conda create --name poetry-py312 'python=3.12'
conda activate poetry-py312

# pipx is recommended, but it requires a brew install on MacOS and I (Raen) avoid brew whenever possible.
# pip seems to work fine.
pip install --upgrade poetry
```

## Install existing dependencies

This repo already contains a poetry.lock file, so running `poetry install` will give you
the exact versions specified there ([Poetry install dependencies](https://python-poetry.org/docs/basic-usage/#installing-dependencies)).

```bash
poetry install
```

If you want to install the docs and tests dependencies as well, use:

```bash
poetry install --with docs,tests
```

## Add a Dependency

Use `poetry add` and then `poetry update`
([Poetry add dependencies](https://python-poetry.org/docs/managing-dependencies/#adding-a-dependency-to-a-group);
see also: [Poetry version-constraint syntax](https://python-poetry.org/docs/dependency-specification/)).
Here are examples:

```bash
# This example adds pandas to the main dependencies.
poetry add pandas

# This example adds sphinx to the docs dependencies.
poetry add sphinx --group docs.dependencies

# Resolve all dependencies and update to latest compatible versions.
poetry update
```

Now commit the updated pyproject.toml and poetry.lock files to the repo.

## Update Dependency Versions

To upgrade to the latest versions compatible with the pyproject.toml file, you have two options below
([Poetry update dependencies](https://python-poetry.org/docs/basic-usage/#updating-dependencies-to-their-latest-versions)):

### Option 1: Simple update using existing environment and lock file

```bash
# This will start from the existing environment and poetry.lock file and update from there.
poetry update
```

Now commit the updated poetry.lock file to the repo.

### Option 2: Clean start and full update

```bash
# --------- Optional Setup --------- #
# Recreate the conda environment named 'poetry-py312'. Be sure to deactivate the environment first.
conda remove --name poetry-py312 --all
conda create --name poetry-py312 'python=3.12'
conda activate poetry-py312
pip install --upgrade poetry
# ---------------------------------- #

# Delete the lock file and rebuild
rm poetry.lock
poetry install --with docs,tests
```

Now commit the updated poetry.lock file to the repo.
