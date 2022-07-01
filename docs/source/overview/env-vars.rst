.. _set env vars:

Set Environment Variables
==========================

(Note: If you are using OAuth2, you need the environment variables described :ref:`here
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

Activate your Conda environment, then:

.. code-block:: bash

    # cd to the environment's directory
    ogdir=$(pwd)
    cd "${CONDA_PREFIX}"

    # if the activate/deactivate files don't already exist, create them
    mkdir -p ./etc/conda/activate.d
    mkdir -p ./etc/conda/deactivate.d
    touch ./etc/conda/activate.d/env_vars.sh
    touch ./etc/conda/deactivate.d/env_vars.sh

    # export variables when environment is activated
    echo "export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}" >> ./etc/conda/activate.d/env_vars.sh
    echo "export GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}" >> ./etc/conda/activate.d/env_vars.sh

    # remove variables when environment is deactivated
    echo "unset GOOGLE_CLOUD_PROJECT" >> ./etc/conda/deactivate.d/env_vars.sh
    echo "unset GOOGLE_APPLICATION_CREDENTIALS" >> ./etc/conda/deactivate.d/env_vars.sh

    # cd back to where you started
    cd "${ogdir}"
