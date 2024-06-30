.. _install:

Install pittgoogle-client
-------------------------

.. automodule:: pittgoogle

Use of a conda environment is recommended (see below).
The basic install command is:

.. code-block:: bash

    pip install pittgoogle-client

The package is imported in python as:

.. code-block:: python

    import pittgoogle

You will need to complete the rest of the :ref:`one-time-setup` before you can and obtain authentication
credentials before you will be able to access data.

Conda
-----

Use of a `conda <https://conda.io/projects/conda>`__ environment is recommended, especially because
it is an easy way to manage the authentication settings in later steps. To create an environment:

.. code-block:: bash

    conda create --name pittgoogle-py311 python=3.11
    conda activate pittgoogle-py311
    pip install pittgoogle-client

You can de-activate and re-activate using:

.. code-block:: bash

    conda deactivate
    conda activate pittgoogle-py311
