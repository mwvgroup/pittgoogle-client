.. _install:

Install pittgoogle-client
----------------------------

.. automodule:: pittgoogle

The basic install command is:

.. code-block:: bash

    pip install pittgoogle-client

This is imported as:

.. code-block:: python

    import pittgoogle

If you have trouble with dependencies, you may want to try creating a
`Conda <https://docs.conda.io/projects/conda/en/latest/index.html>`__ environment
using an environment file that you can download from the repo.

.. code-block:: bash

    # download the file, create, and activate the environment
    wget https://raw.githubusercontent.com/mwvgroup/pittgoogle-client/main/pittgoogle_env.yml
    conda env create --file pittgoogle_env.yml
    conda activate pittgoogle
