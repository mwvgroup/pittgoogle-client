.. _set env vars:

Set Environment Variables
=========================

(Note: If you are using OAuth2, you will also need the environment variables described :ref:`here
<oauth2>`.)

The following environment variables will be used to authenticate you to your Google Cloud project.

-   ``GOOGLE_CLOUD_PROJECT`` -- :ref:`Project ID <find-project-id>` of the project that you will authenticate to.

-   ``GOOGLE_APPLICATION_CREDENTIALS`` -- Path to a key file containing your :ref:`service
    account <service account>` credentials.

Set the environment variables using:

.. code-block:: bash

    # Replace everything between angle brackets with your values.
    export GOOGLE_CLOUD_PROJECT="<my-project-id>"
    export GOOGLE_APPLICATION_CREDENTIALS="</local/path/to/GCP_auth_key.json>"

If you are using pittgoogle-client (python) only, setting the environment variables is sufficient.
If you are also using the command-line tools, you may need to re-run the ``gcloud auth`` command (see :ref:`install gcp cli`).

----

If you are using a conda environment, you can configure it to automatically set/unset the variables when you activate/deactivate the environment.
Otherwise, you will need to set the variables again every time you start a new shell.

First, activate your conda environment and make sure the variables
``GOOGLE_CLOUD_PROJECT`` and ``GOOGLE_APPLICATION_CREDENTIALS`` are set.
Then run the following commands.

.. code-block:: bash

    # Create the activate/deactivate files if they don't already exist.
    mkdir -p "${CONDA_PREFIX}/etc/conda/activate.d"
    mkdir -p "${CONDA_PREFIX}/etc/conda/deactivate.d"
    touch "${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh"
    touch "${CONDA_PREFIX}/etc/conda/deactivate.d/env_vars.sh"

    # Set the environment variables when the environment is activated.
    echo "export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}" >> "${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh"
    echo "export GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}" >> "${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh"

    # Unset the environment variables when the environment is deactivated.
    echo "unset GOOGLE_CLOUD_PROJECT" >> "${CONDA_PREFIX}/etc/conda/deactivate.d/env_vars.sh"
    echo "unset GOOGLE_APPLICATION_CREDENTIALS" >> "${CONDA_PREFIX}/etc/conda/deactivate.d/env_vars.sh"
