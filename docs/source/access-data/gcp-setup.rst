Google Cloud Setup
==================

In order to make API calls you will need to be authenticated to a Google Cloud project.
This page includes a walk through of all the steps you might need to take:

.. contents::
   :local:
   :depth: 1

If you already have access to a Google Cloud project you can pick and choose which
step(s) you need.
Otherwise, it's recommended to follow the steps in order.

Projects are free and are easy to create/delete.
Each user can have many projects simultaneously, and users can share projects.
A basic level of ongoing access to services like Pub/Sub and BigQuery is also free.
No credit card required (see :ref:`/access-data/data-overview:cost`).

.. _setup project:

Setup a Google Cloud Project
--------------------------------

#.  **Create a project**

    -   Go to the
        `Cloud Resource Manager <https://console.cloud.google.com/cloud-resource-manager>`__
        and login with a Google or Gmail account (go
        `here <https://accounts.google.com/signup/v2/webcreateaccount?flowName=GlifWebSignIn&flowEntry=SignUp>`__
        if you need to create one).

    -   Click "Create Project" (A, in the screenshot below).

    -   Enter a project name and **write down the project ID (B)** as you will need it to
        :ref:`set env vars` below, among other things.

    -   Click "Create".

    .. figure:: gcp-setup.png
       :alt: GCP setup


#.     **Enable the APIs**

    Each Cloud service has its own API.
    You can choose which ones you'd like to enable on your project.
    We recommend the following (click the link, then click "Enable"):

    - `Pub/Sub <https://console.cloud.google.com/apis/library/pubsub.googleapis.com>`__ (message streams)

    - `BigQuery <https://console.cloud.google.com/apis/library/bigquery.googleapis.com>`__ (catalogs)

    - `Cloud Storage <https://console.cloud.google.com/apis/library/storage-component.googleapis.com>`__ (file storage)

    If you make an API call to a service that is not enabled in your project,
    the request will be denied and you will be given instructions on how to enable it.
    Alternately, you can search for and enable an API through the
    `API Library <https://console.cloud.google.com/apis/library>`__.

.. _service account:

Create a Service Account and Download a Key File
----------------------------------------------------

3.  Follow Google's instructions to
    `create a service account <https://cloud.google.com/docs/authentication/getting-started#creating_a_service_account>`__
    (ignore the other sections on that page).
    You will:

    -   Create a service account with the **Project > Owner** role (see below).

    -   Download a key file that contains authorization credentials.
        Keep this file secret!
        Take note of the path to the downloaded file, you will need it to
        :ref:`set env vars` below.

    The **Project > Owner** role gives the service account permission to do
    anything and everything, within the project.
    It is the simplest option and allows you to avoid the headache of tracking down
    "permission denied" errors.
    However, this role is excessively permissive in essentially all cases.
    If you want to restrict the permissions granted to the service account, assign a
    different role(s).
    A good place to look is the list of
    `predefined roles <https://cloud.google.com/iam/docs/understanding-roles#predefined>`__.

.. _set env vars:

Set Environment Variables
-----------------------------

For automatic authentication, set the following two environment variables.
Replace everything between angle brackets (``<>``) with your values.
GOOGLE_CLOUD_PROJECT should contain your project ID from :ref:`step a <setup project>`.
GOOGLE_APPLICATION_CREDENTIALS should contain the path to the key file you downloaded in :ref:`step c <service account>`.

.. code-block:: bash

    export GOOGLE_CLOUD_PROJECT=<my-pgb-project>
    export GOOGLE_APPLICATION_CREDENTIALS=</local/path/to/GCP_auth_key.json>

This will allow the APIs to find your key file and authenticate you to your project.

If you are using Conda, the following commands will setup your environment to automatically export these variables upon activation and unset them upon deactivation.

Activate your Conda environment, then:

.. code-block:: bash

    ogdir=$(pwd)
    # make sure the activate/deactivate files exist
    cd $CONDA_PREFIX
    mkdir -p ./etc/conda/activate.d
    mkdir -p ./etc/conda/deactivate.d
    touch ./etc/conda/activate.d/env_vars.sh
    touch ./etc/conda/deactivate.d/env_vars.sh
    # export variables upon activate of the environment
    echo "export GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" >> ./etc/conda/activate.d/env_vars.sh
    echo "export GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS" >> ./etc/conda/activate.d/env_vars.sh
    # unset variables upon deactivate of the environment
    echo 'unset GOOGLE_CLOUD_PROJECT' >> ./etc/conda/deactivate.d/env_vars.sh
    echo 'unset GOOGLE_APPLICATION_CREDENTIALS' >> ./etc/conda/deactivate.d/env_vars.sh
    # return to the original directory

.. _delete-project:

Cleanup: Delete a GCP project
-------------------------------

If you are done with your GCP project you can permanently delete it.
Go to the `Cloud Resource
Manager <https://console.cloud.google.com/cloud-resource-manager>`__,
select your project, and click "DELETE".
