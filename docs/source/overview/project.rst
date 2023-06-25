.. _projects:

Google Cloud Projects
======================

.. contents::
    :depth: 2
    :local:

In order to make API calls accessing data from Pitt-Google's cloud resources you will need to be authenticated to a Google Cloud project.
Projects are free.
They are easy to create and delete.
Each user can have many projects and users can share projects.

.. _setup project:

Setup a Google Cloud project
--------------------------------

**Create a project**

-   Go to the
    `Cloud Resource Manager <https://console.cloud.google.com/cloud-resource-manager>`__
    and login with a Google or Gmail account (go
    `here <https://accounts.google.com/signup/v2/webcreateaccount?flowName=GlifWebSignIn&flowEntry=SignUp>`__
    if you need to create one).

-   Click "Create Project" (A, in the screenshot below).

-   Enter a project name and **write down the project ID (B)** as you will need it to
    :ref:`set env vars`, among other things.

-   Click "Create".

.. figure:: project-setup.png
   :alt: Google Cloud project setup


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

.. _find-project-id:

Where to find the project ID
-----------------------------

Click on the name of the project in the blue menu bar on any page in the
`Google Cloud Console <https://console.cloud.google.com/home/dashboard>`__.
From there you can see the names and IDs of all the projects you are connected to.

.. _delete-project:

Cleanup: Delete a project
-------------------------------

If/when you are done with a Google Cloud project you can permanently delete it.
Go to the `Cloud Resource
Manager <https://console.cloud.google.com/cloud-resource-manager>`__,
select your project, and click "DELETE".
