Google Cloud Setup
==================

In order to make API calls you will need to be authenticated to a Google Cloud project.
This page includes a walk-through of all the steps you might need to take:

.. contents::
   :local:
   :depth: 1

If you already have access to a Google Cloud project, you can pick and choose which
step(s) you need
(e.g., :ref:`download a key file <service account>` and
:ref:`set environment variables <set env vars>`).
Otherwise, it's recommended to follow the steps in order.

Projects are free and easy to create/delete.
Each user can have many projects and users can share projects.

.. _setup project:

Setup a Google Cloud Project
--------------------------------

**Create a project**

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


**Enable the APIs**

Every Google service has at least one API that can be used to access it.
These are disabled by default (since there are hundreds -- Gmail, Maps, Pub/Sub, ...)
They must be manually enabled before anyone in your project can use them.

Enabling the following 3 will be enough for most interactions with
Pitt-Google resources.
Follow the links, make sure you've landed in the right project
(there's a dropdown in the blue menu bar), then click "Enable":

- `Pub/Sub <https://console.cloud.google.com/apis/library/pubsub.googleapis.com>`__

- `BigQuery <https://console.cloud.google.com/apis/library/bigquery.googleapis.com>`__

- `Cloud Storage <https://console.cloud.google.com/apis/library/storage-component.googleapis.com>`__

If/when you attempt a call to an API you have not enabled,
the error message provides instructions to enable it.
You can also search the
`API Library <https://console.cloud.google.com/apis/library>`__.

.. _service account:

Create a Service Account and Download a Key File
----------------------------------------------------

Follow Google's instructions to
`create a service account <https://cloud.google.com/docs/authentication/getting-started#creating_a_service_account>`__
(ignore the other sections on that page -- but first make sure you have access to a
Google Cloud project, described above).
You will:

-   Create a service account with the **Project > Owner** role (see below).

-   Download a key file that contains authorization credentials.
    **Keep this file secret!**
    Take note of the path to the downloaded file, you will need it to
    :ref:`set env vars` below.

Note:
The **Project > Owner** role gives the service account permission to do
anything and everything, within the project.
It is the simplest option and allows you to avoid the headache of tracking down
"permission denied" errors.
However, this role is excessively permissive in essentially all cases.
If you want to restrict the permissions granted to the service account, assign a
different role(s).
A good place to look is:
`Predefined roles <https://cloud.google.com/iam/docs/understanding-roles#predefined>`__.

.. _set env vars:

Set Environment Variables
-----------------------------

It is recommended that you set the following two environment variables.
Doing so allows authentication processes to happen automatically.
(Note: if you are using :doc:`oauth2` you need two other environment variables,
described on that page.)

Replace the angle brackets (``<>``) and everything between them with your values for the
project ID and file path, obtained above.

.. code-block:: bash

    export GOOGLE_CLOUD_PROJECT="<my-project-id>"
    export GOOGLE_APPLICATION_CREDENTIALS="</local/path/to/GCP_auth_key.json>"

If you open a new terminal, you will need to set the variables again.
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

.. _delete-project:

Cleanup: Delete a GCP project
-------------------------------

If/when you are done with a Google Cloud project you can permanently delete it.
Go to the `Cloud Resource
Manager <https://console.cloud.google.com/cloud-resource-manager>`__,
select your project, and click "DELETE".
