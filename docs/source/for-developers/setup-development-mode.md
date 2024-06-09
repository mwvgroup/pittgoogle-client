# Setup Development Mode

Instructions for setting up development or "editable" mode are given below.
This is a method of pip-installing pointed at your local repository so you can iterate code and import changes for testing.

See also: [Python Packaging User Guide](https://packaging.python.org/en/latest/).

When you are ready to release a new version of `pittgoogle-client`, publish to PyPI using the release
process described in [issues #7](https://github.com/mwvgroup/pittgoogle-client/pull/7).

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
```

## Work in development ("editable") mode

Now you can work with the code in your local pittgoogle-client repo in python:

```python
import pittgoogle

# make new changes in your local pittgoogle-client repo code
# then use importlib to reload the package with the new changes
import importlib
importlib.reload(pittgoogle)
# if you don't have access to the new changes at this point, try reloading again
# if that doesn't work, restart your python interpreter
```

See also: [Working in “development mode”](https://packaging.python.org/guides/distributing-packages-using-setuptools/#working-in-development-mode).
