Install pittgoogle-client
----------------------------

.. automodule:: pittgoogle

The basic install command is (but note the recommendations below):

.. code-block:: bash

    pip install pittgoogle-client

This is imported (in python) as:

.. code-block:: python

    import pittgoogle

A Python 3.7 environment is strongly recommended.
A `Conda <https://docs.conda.io/projects/conda/en/latest/index.html>`__ environment
is also recommended.
Here is an example using both:

.. code-block:: bash

    conda create -n pittgoogle python=3.7
    conda activate pittgoogle
    pip install pittgoogle-client

If you have trouble with dependencies, you may want to try creating a Conda environment
using an environment file that you can download from the repo.

.. code-block:: bash

    # download the file, create, and activate the environment
    wget https://raw.githubusercontent.com/mwvgroup/pittgoogle-client/main/pittgoogle_env.yml
    conda env create --file pittgoogle_env.yaml
    conda activate pittgoogle
