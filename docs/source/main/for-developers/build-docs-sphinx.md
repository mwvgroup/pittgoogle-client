# Build Documentation with Sphinx

This page describes how to build documentation locally for testing.
Our published documentation is built automatically when a [new version](release-new-version.md) is released.
Every PR triggers automatic testing of the documentation build, but you can't easily view the built documentation
For those reasons, it is sometimes helpful to be able to build the documentation locally.

1. Follow the setup steps in [Managing Dependencies with Poetry](manage-dependencies-poetry.md) to create a conda environment with Poetry installed. Then:

```bash
# Install pittgoogle dependencies, including those in the "docs" group.
poetry install --with=docs
```

2. Cd to the docs directory and run `make`:

```bash
cd docs  # assuming we started in the repo root directory

# Build the documentation
make html
```

This created a file at `docs/build/html/index.html`.
Open it in a browser to view the documentation.
