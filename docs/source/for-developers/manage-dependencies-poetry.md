# Manage dependencies with Poetry

This page contains instructions for managing the `pittgoogle-client` package dependencies using [Poetry](https://python-poetry.org/).
Poetry was implemented in this repo in [pull #7](https://github.com/mwvgroup/pittgoogle-client/pull/7).

## Setup your environment

Create a new conda environment for poetry and install it ([Poetry installation](https://python-poetry.org/docs/#installation)).
If you already did this, just activate the environment.

```bash
conda create --name poetry-py311 python=3.11
conda activate poetry-py311

# pipx is recommended, but it requires a brew install on MacOS and I (Raen) avoid brew whenever possible.
# pip seems to work fine.
pip install poetry
```

If you come back to this later you may need to reactivate your environment.

```bash
conda activate poetry-py311
```

If you want to start over with a fresh environment, deactivate the environment and remove it.

```bash
conda deactivate
conda remove --name poetry-py311 --all
```

## Install existing dependencies

This repo already contains a poetry.lock file, so running `poetry install` will give you
the exact versions specified there ([Poetry install dependencies](https://python-poetry.org/docs/basic-usage/#installing-dependencies)).

If you would rather start over completely, skip ahead to the next section.

```bash
poetry install
```

If you want to install the docs dependencies as well, use:

```bash
poetry install --extras=docs
```

## Update Dependency Versions

To upgrade to the latest versions compatible with the pyproject.toml file, you have two options below
([Poetry update dependencies](https://python-poetry.org/docs/basic-usage/#updating-dependencies-to-their-latest-versions)):

```bash
# Option 1: Start over completely by deleting the lock file and re-installing.
rm poetry.lock
poetry install

# Option 2: Update dependencies starting from the existing lock file (assumes you've run poetry install).
poetry update
```

Now commit the updated poetry.lock file to the repo.

## Add a Dependency

Here are two examples
([Poetry add dependencies](https://python-poetry.org/docs/managing-dependencies/#adding-a-dependency-to-a-group),
see also: [Poetry version-constraint syntax](https://python-poetry.org/docs/dependency-specification/)):

```bash
# This example adds pandas to the main dependencies.
poetry add pandas

# This example adds sphinx to the docs dependencies.
poetry add sphinx --group docs.dependencies
```
