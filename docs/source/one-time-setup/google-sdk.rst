.. _install gcp cli:

Google Cloud SDK
========================

.. note::

    This page contains instructions for installing command-line tools.
    This is not required in order to use ``pittgoogle-client`` itself but
    is helpful for some use cases. If you don't know whether you need this,
    skip it for now.

The Google Cloud command-line tools include
`default components <https://cloud.google.com/sdk/docs/components#default_components>`__:
``gcloud``, ``bq``, and ``gsutil``.

For complete install instructions, see `Install the gcloud CLI  <https://cloud.google.com/sdk/docs/install>`__
Windows users will need to use the installer found at that link.
For Linux and Mac, the basic command is:

.. code-block:: bash

    curl https://sdk.cloud.google.com | bash

In either case, follow the instructions to complete the installation.
Then, open a new terminal or restart your shell.
Make sure your :ref:`environment variables <set env vars>` are set, reset them if needed.
Then initialize gcloud using:

.. code-block:: bash

    gcloud init

and follow the directions.
You will likely need to authenticate using the Gmail address (or similar) that is registered with your Google Cloud project.
Note that this may open a browser and ask you to complete the setup there.

The remaining steps are recommended but optional.

Set your new project as the default:

.. code-block:: bash

    gcloud config set project "$GOOGLE_CLOUD_PROJECT"

Instruct gcloud to authenticate using your key file containing
:ref:`service account credentials <service account>`:

.. code-block:: bash

    gcloud auth activate-service-account \
        --project="$GOOGLE_CLOUD_PROJECT" \
        --key-file="$GOOGLE_APPLICATION_CREDENTIALS"

You may want to `create a configuration <https://cloud.google.com/sdk/docs/configurations>`__ if you use multiple projects or want to control settings like the default region.

..
    # [TODO] give instructions to add the ``gcloud auth`` command to the conda activation file and/or to create a configuration and activate it with the conda env.
