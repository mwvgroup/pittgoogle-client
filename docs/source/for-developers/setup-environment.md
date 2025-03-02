# Set up and use a developer environment

Instructions for setting up an environment with `pittgoogle-client` installed in development or "editable"
mode are given below.
This is a method of pip-installing the package from your local files so that you have quick access to
your changes as you develop code.

See also: [Working in “development mode”](https://packaging.python.org/guides/distributing-packages-using-setuptools/#working-in-development-mode).

## Setup

```bash
# clone the repo and cd in
git clone https://github.com/mwvgroup/pittgoogle-client.git
cd pittgoogle-client

# recommended to create a new conda env
# use the latest python version unless you have a specific reason not to
conda create --name pittgoogle python=3.12
conda activate pittgoogle

# install pittgoogle-client in editable mode. use pwd so that the absolute path is registered.
pip install -e $(pwd)

pip install --upgrade poetry
poetry install --with docs,tests
```

## Work

Now you can work with the code in your local pittgoogle-client repo in python:

```python
import importlib
import pittgoogle

# do your testing
# make new changes in your local pittgoogle-client repo code
# then use importlib to reload the package with the new changes

importlib.reload(pittgoogle)
# if you don't have access to the new changes at this point, try reloading again
# if that doesn't work, restart your python interpreter
```
