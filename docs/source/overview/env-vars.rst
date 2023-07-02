.. _set env vars:

Set Environment Variables
==========================

(Note: If you are using OAuth2, you will also need the environment variables described :ref:`here
<oauth2>`.)

Setting these two environment variables will support a smooth authentication process
that occurs in the background:

-   `GOOGLE_CLOUD_PROJECT` -- Project ID of the :ref:`project <projects>` that you
    will authenticate to.

-   `GOOGLE_APPLICATION_CREDENTIALS` -- Path to a key file containing your :ref:`service
    account <service account>` credentials.

To set these, replace the following angle brackets (``<>``) and everything between them with your
values.

.. code-block:: bash

    export GOOGLE_CLOUD_PROJECT="<my-project-id>"
    export GOOGLE_APPLICATION_CREDENTIALS="</local/path/to/GCP_auth_key.json>"

**If you open a new terminal, you will need to set the variables again.**
Conda can simplify this.
The following commands will configure it to automatically set these
variables when your environment is activated, and erase them when it is deactivated.

Activate your Conda environment and make sure the variables
``GOOGLE_CLOUD_PROJECT`` and ``GOOGLE_APPLICATION_CREDENTIALS`` are set.
Then:

.. code-block:: bash

    # create the activate/deactivate files if they don't already exist
    mkdir -p "${CONDA_PREFIX}/etc/conda/activate.d"
    mkdir -p "${CONDA_PREFIX}/etc/conda/deactivate.d"
    touch "${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh"
    touch "${CONDA_PREFIX}/etc/conda/deactivate.d/env_vars.sh"

    # store the variables to export them automatically when the environment is activated
    echo "export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}" >> "${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh"
    echo "export GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}" >> "${CONDA_PREFIX}/etc/conda/activate.d/env_vars.sh"

    # remove the variables automatically when the environment is deactivated
    echo "unset GOOGLE_CLOUD_PROJECT" >> "${CONDA_PREFIX}/etc/conda/deactivate.d/env_vars.sh"
    echo "unset GOOGLE_APPLICATION_CREDENTIALS" >> "${CONDA_PREFIX}/etc/conda/deactivate.d/env_vars.sh"
