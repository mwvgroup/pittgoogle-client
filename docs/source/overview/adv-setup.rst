Advanced Setup
===============

.. note::

    Nothing on this page is required for standard access.
    In most cases, you should just :doc:`install-pittgoogle` instead.

Install Libraries for Google Cloud APIs
----------------------------------------

If you want to install python libraries individually or install command-line tools,
read on.

.. _install gcp python:

Python
~~~~~~~~~~~~~~~~

You can pip install any of the Google Cloud python libraries.
Here are the 3 we use most.

.. code-block:: bash

    pip install google-cloud-bigquery
    pip install google-cloud-pubsub
    pip install google-cloud-storage

Here is a complete list:
`Python Cloud Client Libraries <https://cloud.google.com/python/docs/reference>`__.

.. _install gcp cli:

Command Line
~~~~~~~~~~~~~~~~

The Google Cloud SDK includes the 3 command line tools: gcloud, bq, and gsutil (see
`default components <https://cloud.google.com/sdk/docs/components#default_components>`__
).

To install on Windows, use the
`installer <https://cloud.google.com/sdk/docs/downloads-interactive#windows>`__.
For Linux and Mac, use:

.. code-block:: bash

    curl https://sdk.cloud.google.com | bash

In either case, follow the instructions to complete the installation.
Then open a new terminal or restart your shell.
Make sure your :ref:`environment variables <set env vars>` are set, reset them if needed.
Then initialize gcloud using

.. code-block:: bash

    gcloud init

and follow the directions.
Note that this may open a browser and ask you to complete the setup there.

The remaining steps are optional, but recommended for the smoothest experience.

Set your new project as the default:

.. code-block:: bash

    gcloud config set project "$GOOGLE_CLOUD_PROJECT"

Instruct gcloud to authenticate using your key file containing
:ref:`service account credentials <service account>`:

.. code-block:: bash

    gcloud auth activate-service-account \
        --project="$GOOGLE_CLOUD_PROJECT" \
        --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
