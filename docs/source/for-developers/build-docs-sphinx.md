# Build documentation with Sphinx

This page describes how to build documentation locally for testing.
This is not always needed.
Our published documentation is built and released automatically when a
[new package version](release-new-version.md) is released.
In addition, every PR triggers automatic testing of the documentation build.
However, those GitHub builds can take awhile and there doesn't seem to be an easy way to actually
view the built documentation.
For those reasons, it is sometimes helpful to be able to build the documentation locally.

Follow the setup steps in [Managing Dependencies with Poetry](manage-dependencies-poetry.md) to
create a conda environment with Poetry installed. Then:

```bash
# Install pittgoogle dependencies, including those in the "docs" group.
poetry install --with docs
```

Now, `cd` to the docs directory and run `make`:

```bash
cd docs  # assuming we started in the repo root directory

# Build the documentation
make clean
make html
```

This should have created a file at `docs/build/html/index.html`.
Open it in a browser to view the built documentation.
