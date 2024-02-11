# PyPI Setup

Typical workflow:

1. While developing pittgoogle-client, work in "editable" mode. This is a way of pip-installing the package from the source code in your local directory, which gives you immediate access to your changes (though you may need to re-import the package or re-load the python environment).

2. When ready, publish the package to TestPyPI, pip-install from there and test.

3. When ready, publicly release a new version by publishing to PyPI. This is now handled through the release process described in [issues #7](https://github.com/mwvgroup/pittgoogle-client/pull/7). Instructions to do this manually are included below as an FYI, but should not be needed for this repo.

See also: [Python Packaging User Guide](https://packaging.python.org/en/latest/).

## Setup

```bash
# clone the repo and cd in
git clone https://github.com/mwvgroup/pittgoogle-client.git
cd pittgoogle-client
```

## Work in development ("editable") mode:

```bash
# recommended to create a new conda env
# use the latest python version unless you have a specific reason not to
conda create --name pittgoogle python=3.12
conda activate pittgoogle

# install pittgoogle-client in editable mode. use pwd so that the absolute path is registered.
pip install -e $(pwd)
```

Now you can work with the code in your local pittgoogle-client repo in python:

```python
import pittgoogle

# make new changes in your local pittgoogle-client repo
# then, reload the package to access the new changes
import importlib
importlib.reload(pittgoogle)
# if you don't have access to the new changes at this point, try reloading again

# some types of changes cannot be accessed by simply reloading the package
# so if you still don't have access to the new changes, restart your python interpreter
```

See also: [Working in “development mode”](https://packaging.python.org/guides/distributing-packages-using-setuptools/#working-in-development-mode).

## Build the distribution and upload it to testpypi

You will need an account on TestPyPI. See Python Packaging User Guide: [Uploading the distribution archives](https://packaging.python.org/en/latest/tutorials/packaging-projects/#uploading-the-distribution-archives).

```bash
# you may want to activate a conda environment first
# you may need to install some tools by uncommenting the following line
# python -m pip install --upgrade pip setuptools wheel build twine

python3 -m build
python3 -m twine upload --repository testpypi dist/*
```

This will print some information to stdout, including links to the package version(s).

## Build the distribution and upload it to PyPI

This is now handled through the release process described in [issues #7](https://github.com/mwvgroup/pittgoogle-client/pull/7). Instructions to do this manually are included below as an FYI, but should not be needed for this repo.

You will need an account on PyPI. See Python Packaging User Guide: [Next steps](https://packaging.python.org/en/latest/tutorials/packaging-projects/#next-steps).

```bash
# you may want to activate a conda environment first
# you may need to install some tools by uncommenting the following line
# python -m pip install --upgrade pip setuptools wheel build twine

python3 -m build
python3 -m twine upload dist/*
```

This will print some information to stdout, including links to the package version(s).
